import logging
import re
from celery import shared_task
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime

from users.models import User, ConsumerInterest
from handyman.models import Handyman, HandymanPromotion, PromotionNotification

logger = logging.getLogger(__name__)

@shared_task(name="match_handyman_services")
def match_handyman_services(force_match=False, dry_run=False):
    """
    Celery task to match handyman services with consumer interests
    
    Args:
        force_match (bool): Whether to ignore notification preferences
        dry_run (bool): Whether to actually send emails or just simulate
        
    Returns:
        dict: Statistics about the matching process
    """
    logger.info(f"Starting handyman matching task (force_match={force_match}, dry_run={dry_run})")
    
    today = timezone.now().date()
    
    # Track statistics
    stats = {
        'total_matches': 0,
        'total_emails': 0,
        'consumers_matched': set(),
        'promotions_matched': set(),
        'skipped_no_business_card': 0,
        'skipped_no_description': 0,
        'skipped_notification_pref': 0,
        'skipped_already_notified': 0,
    }
    
    # Get active handyman promotions
    active_promotions = HandymanPromotion.objects.filter(
        is_active=True,
        start_date__lte=today,
        end_date__gte=today
    ).select_related('handyman', 'handyman__user')
    
    if not active_promotions.exists():
        logger.warning('No active handyman promotions found')
        return stats
    
    # Get consumers who want to receive notifications
    consumers = User.objects.filter(
        user_type='requestor',
        is_active=True  # Only consider active users
    ).prefetch_related('interests', 'profile')
    
    logger.info(f'Found {active_promotions.count()} active handyman promotions')
    logger.info(f'Processing {consumers.count()} potential consumers')
    
    # For each promotion, find matching consumers
    for promotion in active_promotions:
        handyman = promotion.handyman
        handyman_user = handyman.user
        
        # Skip if handyman doesn't have a business card
        if not handyman_user.business_card_front:
            logger.warning(f'Skipping handyman {handyman.id}: No business card front image')
            stats['skipped_no_business_card'] += 1
            continue
            
        # Get handyman's service description
        service_description = handyman.detailed_services_description or handyman_user.service_description or ''
        if not service_description:
            logger.warning(f'Skipping handyman {handyman.id}: No service description')
            stats['skipped_no_description'] += 1
            continue
        
        matched_consumers = []
        
        # Find consumers interested in services similar to this handyman's offerings
        for consumer in consumers:
            # Skip consumers who already received this promotion
            already_notified = PromotionNotification.objects.filter(
                promotion=promotion,
                recipient=consumer
            ).exists()
            
            if already_notified:
                stats['skipped_already_notified'] += 1
                continue
                
            # Get consumer interests
            try:
                interest = ConsumerInterest.objects.get(user=consumer)
                
                # Skip if notifications are disabled (unless forced)
                if not interest.receive_notifications and not force_match:
                    stats['skipped_notification_pref'] += 1
                    continue
                
                # Check discount threshold preference (unless forced)
                if not force_match and interest.notification_preference == 'discount':
                    if promotion.discount_percentage < interest.min_discount_threshold:
                        stats['skipped_notification_pref'] += 1
                        continue
                    
                # Check if consumer profile contains relevant service interests
                if hasattr(consumer, 'profile') and consumer.profile:
                    consumer_interest_text = consumer.profile.bio or ''
                else:
                    consumer_interest_text = ''
                    
                if not consumer_interest_text:
                    continue
                    
                # Perform enhanced full-text matching
                match_score = calculate_match_score(service_description, consumer_interest_text)
                
                # Consider it a match if score is above threshold
                if match_score >= 0.2:  # 20% similarity threshold
                    matched_consumers.append((consumer, match_score))
                    stats['consumers_matched'].add(consumer.id)
                    stats['promotions_matched'].add(promotion.id)
                    stats['total_matches'] += 1
                    
            except ConsumerInterest.DoesNotExist:
                continue
        
        # Sort matched consumers by match score (highest first)
        matched_consumers.sort(key=lambda x: x[1], reverse=True)
        matched_consumers = [consumer for consumer, _ in matched_consumers]
        
        # Send emails to matched consumers
        if matched_consumers and not dry_run:
            for consumer in matched_consumers:
                if send_promotional_email(consumer, promotion, handyman):
                    stats['total_emails'] += 1
        
        logger.info(f'Matched promotion #{promotion.id} with {len(matched_consumers)} consumers')
    
    # Log final statistics
    logger.info(f'Completed matching process')
    logger.info(f'Total matches found: {stats["total_matches"]}')
    logger.info(f'Unique consumers matched: {len(stats["consumers_matched"])}')
    logger.info(f'Promotions that found matches: {len(stats["promotions_matched"])}')
    logger.info(f'Skipped (no business card): {stats["skipped_no_business_card"]}')
    logger.info(f'Skipped (no description): {stats["skipped_no_description"]}')
    logger.info(f'Skipped (notification preference): {stats["skipped_notification_pref"]}')
    logger.info(f'Skipped (already notified): {stats["skipped_already_notified"]}')
    
    if not dry_run:
        logger.info(f'Total emails sent: {stats["total_emails"]}')
    else:
        logger.info(f'Dry run - {stats["total_emails"]} emails would have been sent')
    
    # Convert sets to counts for serialization
    consumers_matched_count = len(stats['consumers_matched'])
    promotions_matched_count = len(stats['promotions_matched'])
    
    # Create a new dict with serializable values
    result_stats = {
        'total_matches': stats['total_matches'],
        'total_emails': stats['total_emails'],
        'consumers_matched': consumers_matched_count,
        'promotions_matched': promotions_matched_count,
        'skipped_no_business_card': stats['skipped_no_business_card'],
        'skipped_no_description': stats['skipped_no_description'],
        'skipped_notification_pref': stats['skipped_notification_pref'],
        'skipped_already_notified': stats['skipped_already_notified'],
    }
    
    return result_stats


@shared_task(name="send_handyman_promotional_email")
def send_promotional_email_task(consumer_id, promotion_id):
    """
    Send a single promotional email as a separate Celery task
    
    Args:
        consumer_id (int): The ID of the consumer to email
        promotion_id (int): The ID of the promotion to send
    
    Returns:
        bool: Whether the email was sent successfully
    """
    try:
        consumer = User.objects.get(id=consumer_id)
        promotion = HandymanPromotion.objects.get(id=promotion_id)
        handyman = promotion.handyman
        
        return send_promotional_email(consumer, promotion, handyman)
    except (User.DoesNotExist, HandymanPromotion.DoesNotExist) as e:
        logger.error(f"Error sending promotional email: {str(e)}")
        return False


def send_promotional_email(consumer, promotion, handyman):
    """Send promotional email to a consumer about a handyman service"""
    try:
        handyman_user = handyman.user
        
        # Create email context
        context = {
            'consumer_name': consumer.get_full_name() or consumer.email,
            'handyman_name': handyman.business_name or handyman_user.get_full_name(),
            'discount_percentage': promotion.discount_percentage,
            'promo_description': promotion.description,
            'promo_code': promotion.code,
            'start_date': promotion.start_date,
            'end_date': promotion.end_date,
            'business_card_front': handyman_user.business_card_front.url if handyman_user.business_card_front else None,
            'business_card_back': handyman_user.business_card_back.url if handyman_user.business_card_back and not handyman_user.has_blank_card_back else None,
            'service_description': handyman.detailed_services_description or handyman_user.service_description or '',
            'handyman_email': handyman_user.email,
            'handyman_phone': handyman_user.phone_number or 'Not provided',
            'current_year': datetime.now().year,
        }
        
        # Create the email
        subject = f"Special Discount Offer for Handyman Services"
        from_email = settings.DEFAULT_FROM_EMAIL
        to_email = consumer.email
        
        # Plain text version
        text_content = f"""
Hi {context['consumer_name']},

This is the Admin from the Handyman Platform. Good news! We found a business that is currently offering a discount that matches what you have indicated you're looking for.

Please contact the business at your convenience for your project. Below is the discount offering from the business:

{promotion.description}

Discount: {promotion.discount_percentage}% OFF
Valid: {promotion.start_date} to {promotion.end_date}
Promo Code: {promotion.code}

Business: {context['handyman_name']}
Contact: {context['handyman_email']} | {context['handyman_phone']}

Thank you for using our platform!
        """
        
        # HTML version
        html_content = render_to_string('handyman/emails/promotion_match.html', context)
        
        # Create and send the email
        email = EmailMultiAlternatives(subject, text_content, from_email, [to_email])
        email.attach_alternative(html_content, "text/html")
        
        # Send the email
        email.send()
        
        # Record that this notification was sent
        PromotionNotification.objects.create(
            promotion=promotion,
            recipient=consumer
        )
        
        logger.info(f"Sent promotion email to {consumer.email} for handyman {handyman.id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send promotion email to {consumer.email}: {str(e)}")
        return False


def calculate_match_score(service_description, consumer_interest_text):
    """
    Calculate a match score between service description and consumer interest text
    Returns a value between 0 and 1, where higher means better match
    """
    # Convert both texts to lowercase for case-insensitive matching
    service_desc_lower = service_description.lower()
    interest_text_lower = consumer_interest_text.lower()
    
    # Clean and tokenize text (remove punctuation and split into words)
    service_words = set(re.sub(r'[^\w\s]', ' ', service_desc_lower).split())
    interest_words = set(re.sub(r'[^\w\s]', ' ', interest_text_lower).split())
    
    # Common stop words to exclude
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'in', 'to', 
                 'for', 'with', 'on', 'at', 'from', 'by', 'of', 'this', 'that', 
                 'i', 'you', 'he', 'she', 'it', 'we', 'they'}
    
    # Remove stop words
    service_words = service_words - stop_words
    interest_words = interest_words - stop_words
    
    # Remove very short words (typically not meaningful)
    service_words = {word for word in service_words if len(word) > 2}
    interest_words = {word for word in interest_words if len(word) > 2}
    
    if not service_words or not interest_words:
        return 0
    
    # Find common words
    common_words = service_words.intersection(interest_words)
    
    # Calculate Jaccard similarity for words
    word_similarity = len(common_words) / (len(service_words) + len(interest_words) - len(common_words))
    
    # Check for phrase matches (bigrams and trigrams)
    service_bigrams = get_ngrams(service_desc_lower, 2)
    interest_bigrams = get_ngrams(interest_text_lower, 2)
    common_bigrams = service_bigrams.intersection(interest_bigrams)
    
    # Calculate similarity scores
    bigram_similarity = 0
    if service_bigrams and interest_bigrams:
        bigram_similarity = len(common_bigrams) / max(1, (len(service_bigrams) + len(interest_bigrams) - len(common_bigrams)))
    
    # Check for specific keywords that would strongly indicate a match
    service_keywords = {'plumb', 'electr', 'paint', 'repair', 'fix', 'install', 'build', 
                      'renovat', 'construct', 'clean', 'mow', 'garden', 'roof', 'floor', 
                      'wall', 'cabinet', 'tile', 'bathroom', 'kitchen'}
    
    keyword_matches = sum(1 for word in service_words if any(keyword in word for keyword in service_keywords)) + \
                     sum(1 for word in interest_words if any(keyword in word for keyword in service_keywords))
    
    keyword_bonus = min(0.3, keyword_matches * 0.05)  # Cap at 0.3
    
    # Combined score with weightings
    score = (word_similarity * 0.5) + (bigram_similarity * 0.3) + keyword_bonus
    
    return min(1.0, score)  # Cap at 1.0


def get_ngrams(text, n):
    """Generate n-grams from text"""
    words = text.split()
    ngrams = set()
    for i in range(len(words) - n + 1):
        ngrams.add(' '.join(words[i:i+n]))
    return ngrams 