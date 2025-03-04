from django.apps import apps as django_apps
from django.forms import ValidationError
from edc_constants.constants import YES, NO
from edc_form_validators import FormValidator

from .crf_offstudy_form_validator import CrfOffStudyFormValidator
from .form_validator_mixin import ChildFormValidatorMixin


class InfantFeedingFormValidator(ChildFormValidatorMixin,
                                 CrfOffStudyFormValidator,
                                 FormValidator):

    breast_feeding_model = 'flourish_caregiver.breastfeedingquestionnaire'

    def clean(self):
        self.subject_identifier = self.cleaned_data.get(
            'child_visit').appointment.subject_identifier
        super().clean()

        self.validate_consent_version_obj(self.subject_identifier)

        self.validate_against_visit_datetime(
            self.cleaned_data.get('report_datetime'))

        self.breastfeeding_validations()

        self.formula_validations()

        self.other_liquids_validations()

        self.solid_foods_validations()

    def previous_feeding_instance(self):
        infant_feeding_cls = django_apps.get_model('flourish_child.infantfeeding')

        child_visit = self.cleaned_data.get('child_visit')

        while child_visit.get_previous_by_report_datetime():

            child_visit = child_visit.get_previous_by_report_datetime()

            try:
                infant_feeding_cls.objects.get(
                    child_visit=child_visit)
            except infant_feeding_cls.DoesNotExist:
                continue
            else:
                return True

    def breastfeeding_validations(self):

        fields_required = ['bf_start_dt', 'bf_start_dt_est', 'recent_bf_dt',
                           'continuing_to_bf']
        for field in fields_required:
            self.required_if(
                YES,
                field='ever_breastfed',
                field_required=field)

        if self.previous_feeding_instance():
            self.required_if(
                YES,
                field='child_weaned',
                field_required='dt_weaned')
        else:
            self.required_if(
                NO,
                field='continuing_to_bf',
                field_required='dt_weaned')

        self.applicable_if(
            YES,
            field='ever_breastfed',
            field_applicable='freq_milk_rec')

        self.required_if(
            YES,
            field='rec_liquids',
            field_required='took_formula')

    def formula_validations(self):

        self.required_if(
            YES,
            field='took_formula',
            field_required='dt_formula_introduced')

        self.required_if_not_none(
            field='dt_formula_introduced',
            field_required='dt_formula_est')

        self.required_if(
            YES,
            field='took_formula',
            field_required='formula_feedng_completd')

        fields_required = ['dt_formula_stopd', 'dt_stopd_est']
        for field in fields_required:
            self.required_if(
                YES,
                field='formula_feedng_completd',
                field_required=field)

        self.required_if(
            NO,
            field='formula_feedng_completd',
            field_required='formula_water')

        self.validate_other_specify(field='formula_water')

    def other_liquids_validations(self):

        for field in ['taken_water', 'taken_juice', 'taken_cows_milk',
                      'taken_animal_milk', 'taken_salts']:
            self.required_if(
                YES,
                field='rec_liquids',
                field_required=field)

        self.applicable_if(
            YES,
            field='taken_cows_milk',
            field_applicable='cows_milk_prep')

        for field in ['animal_milk_specify', 'milk_boiled']:
            self.required_if(
                YES,
                field='taken_animal_milk',
                field_required=field)

    def solid_foods_validations(self):

        for field in ['solid_foods_dt', 'solid_foods_age']:
            self.required_if(
                YES,
                field='taken_solid_foods',
                field_required=field)

        self.m2m_required_if(
            YES,
            field='taken_solid_foods',
            m2m_field='solid_foods')

        solid_foods = self.cleaned_data.get('solid_foods')
        selected = [solid.short_name for solid in solid_foods]
        value_field = {'food_grains': 'grain_intake_freq',
                       'food_legume': 'legumes_intake_freq',
                       'food_dairy': 'dairy_intake_freq',
                       'food_flesh': 'flesh_foods_freq',
                       'food_eggs': 'eggs_intake_freq',
                       'food_porridge': 'porridge_intake_freq',
                       'food_vita': 'vitamin_a_fruits_freq',
                       'food_fruitsvege': ['other_fruits_vegies', 'other_fruits_freq'],
                       'food_othersolid': ['other_solids', 'other_solids_freq']}

        for value, field in value_field.items():
            if isinstance(field, list):
                for required in field:
                    self.required_if_true(
                        value in selected,
                        field_required=required)
            else:
                self.required_if_true(
                    value in selected,
                    field_required=field)
