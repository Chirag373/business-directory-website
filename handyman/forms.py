from django import forms
from .models import Service
from django.utils import timezone


class HandymanSignupForm(forms.Form):
    """Form for handyman signup"""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=True)
    business_name = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False)

    address_number = forms.CharField(max_length=20, required=True)
    address = forms.CharField(max_length=100, required=True)
    country = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    city = forms.CharField(max_length=100, required=True)
    zip = forms.CharField(max_length=20, required=True)

    service_description = forms.CharField(widget=forms.Textarea, required=True)
    service_categories = forms.MultipleChoiceField(
        choices=[
            ("Plumbing", "Plumbing"),
            ("Electrical", "Electrical"),
            ("Carpentry", "Carpentry"),
            ("Painting", "Painting"),
            ("Landscaping", "Landscaping"),
            ("General Repairs", "General Repairs"),
            ("HVAC", "HVAC"),
            ("Roofing", "Roofing"),
            ("Cleaning", "Cleaning"),
            ("Flooring", "Flooring"),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )

    run_promotion = forms.BooleanField(required=False)
    discount_percentage = forms.IntegerField(required=False)
    discount_description = forms.CharField(max_length=200, required=False)

    card_front = forms.ImageField(required=True)
    card_back = forms.ImageField(required=False)
    blank_back = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        run_promotion = cleaned_data.get("run_promotion")
        discount_percentage = cleaned_data.get("discount_percentage")

        if run_promotion and not discount_percentage:
            self.add_error(
                "discount_percentage",
                "Discount percentage is required when running a promotion",
            )

        card_back = cleaned_data.get("card_back")
        blank_back = cleaned_data.get("blank_back")

        if not card_back and not blank_back:
            self.add_error(
                "card_back",
                "Either upload a back side image or check the blank back checkbox",
            )

        return cleaned_data


class HandymanProfileUpdateForm(forms.Form):
    """Form for updating handyman profile details"""

    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    email = forms.EmailField(required=True, disabled=True)
    phone_number = forms.CharField(max_length=15, required=True)

    business_name = forms.CharField(max_length=100, required=True)
    website = forms.URLField(required=False)

    bio = forms.CharField(widget=forms.Textarea, required=False)
    experience_years = forms.IntegerField(min_value=0, required=False)
    license_number = forms.CharField(max_length=50, required=False)

    is_insured = forms.BooleanField(required=False)
    is_licensed = forms.BooleanField(required=False)

    detailed_services_description = forms.CharField(
        widget=forms.Textarea, required=True
    )

    street = forms.CharField(max_length=255, required=True, label="Street Address")
    city = forms.CharField(max_length=100, required=True)
    state = forms.CharField(max_length=100, required=True)
    postal_code = forms.CharField(max_length=20, required=True, label="ZIP/Postal Code")
    country = forms.CharField(max_length=100, required=True, initial="United States")

    profile_picture = forms.ImageField(required=False)


class BusinessCardUpdateForm(forms.Form):
    """Form for updating business card images"""

    card_front = forms.ImageField(required=True)
    card_back = forms.ImageField(required=False)
    blank_back = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        card_back = cleaned_data.get("card_back")
        blank_back = cleaned_data.get("blank_back")

        if not card_back and not blank_back:
            self.add_error(
                "card_back",
                "Either upload a back side image or check the blank back checkbox",
            )

        return cleaned_data


class HandymanServicesForm(forms.Form):
    """Form for updating handyman services"""

    service_description = forms.CharField(widget=forms.Textarea, required=True)
    service_categories = forms.MultipleChoiceField(
        required=True,
        widget=forms.CheckboxSelectMultiple,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Get all available services dynamically
        service_choices = [
            (service.name, service.name) for service in Service.objects.all()
        ]

        # Default choices if no services exist in database or to ensure all standard categories are available
        default_choices = [
            ("Plumbing", "Plumbing"),
            ("Electrical", "Electrical"),
            ("Carpentry", "Carpentry"),
            ("Painting", "Painting"),
            ("Landscaping", "Landscaping"),
            ("General Services", "General Services"),
            ("HVAC", "HVAC"),
            ("Roofing", "Roofing"),
            ("Cleaning", "Cleaning"),
            ("Flooring", "Flooring"),
            ("Concrete", "Concrete"),
            ("Drywall", "Drywall"),
            ("Appliance Repair", "Appliance Repair"),
        ]

        # Combine existing services with default choices, avoiding duplicates
        existing_service_names = [choice[0] for choice in service_choices]
        for default_choice in default_choices:
            if default_choice[0] not in existing_service_names:
                service_choices.append(default_choice)

        self.fields["service_categories"].choices = service_choices

    def clean_service_categories(self):
        """
        Custom validation for service categories to allow new categories
        that might not be in the database yet
        """
        categories = self.cleaned_data.get("service_categories")
        if not categories:
            raise forms.ValidationError("Please select at least one service category.")

        # Instead of strict validation, accept all provided categories
        # They will be created in the view if they don't exist
        return categories


class HandymanPromotionForm(forms.Form):
    """Form for creating handyman promotional offers"""

    run_campaign = forms.BooleanField(required=False, initial=False)
    discount_description = forms.CharField(max_length=200, required=False)
    discount_percentage = forms.IntegerField(required=False, min_value=1, max_value=100)
    promo_code = forms.CharField(max_length=20, required=False)
    start_date = forms.DateField(required=False)
    stop_date = forms.DateField(required=False)

    def clean(self):
        cleaned_data = super().clean()
        run_campaign = cleaned_data.get("run_campaign")

        if run_campaign:
            # Required fields when running a campaign
            required_fields = [
                "discount_description",
                "discount_percentage",
                "promo_code",
                "start_date",
                "stop_date",
            ]
            for field in required_fields:
                if not cleaned_data.get(field):
                    self.add_error(
                        field,
                        f"{field.replace('_', ' ').title()} is required when running a promotion.",
                    )

            # Date validation
            start_date = cleaned_data.get("start_date")
            stop_date = cleaned_data.get("stop_date")

            if start_date and stop_date and start_date >= stop_date:
                self.add_error("stop_date", "End date must be after start date.")

            if start_date and start_date < timezone.now().date():
                self.add_error("start_date", "Start date cannot be in the past.")

        return cleaned_data


class JobRequestForm(forms.Form):
    """Form for creating job requests"""

    handyman_id = forms.IntegerField(required=True)
    service_id = forms.IntegerField(required=True)
    description = forms.CharField(widget=forms.Textarea, required=True)
    scheduled_date = forms.DateField(required=True)
    scheduled_time = forms.TimeField(required=True)

    # Address fields
    address_number = forms.CharField(max_length=20, required=True)
    address_street = forms.CharField(max_length=100, required=True)
    address_city = forms.CharField(max_length=100, required=True)
    address_state = forms.CharField(max_length=100, required=True)
    address_zip = forms.CharField(max_length=20, required=True)
    address_country = forms.CharField(max_length=100, required=False, initial="USA")

    # Optional promotion code
    promo_code = forms.CharField(max_length=20, required=False)

    def clean(self):
        cleaned_data = super().clean()
        scheduled_date = cleaned_data.get("scheduled_date")

        if scheduled_date and scheduled_date < timezone.now().date():
            self.add_error("scheduled_date", "Scheduled date cannot be in the past.")

        return cleaned_data


class JobRequestUpdateForm(forms.Form):
    """Form for updating job request status"""

    job_id = forms.IntegerField(required=True)
    action = forms.ChoiceField(
        choices=[
            ("accept", "Accept"),
            ("decline", "Decline"),
            ("complete", "Complete"),
        ],
        required=True,
    )
