from django.apps import apps as django_apps
from edc_form_validators import FormValidator
from edc_constants.constants import OTHER
from ..form_validator_mixin import ChildFormValidatorMixin

class HivKnowledgeFormValidator(ChildFormValidatorMixin, FormValidator):
      
      
      def clean(self):
          super().clean()
          
          self.m2m_other_specify(OTHER, 
                                 m2m_field='hiv_knowledge_medium', 
                                 field_other='hiv_knowledge_medium_other')
          
          self.required_if(OTHER,
                           field='hiv_community_treatment',
                           field_required='hiv_community_treatment_other')