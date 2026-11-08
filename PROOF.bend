import Base
import ./LAWS.bend as Requirements
import ./ui_policy.bend as UI
import ./ui/home/model.bend as Home

def Requirements.ui_external_has_no_mapping():
  {==}

def Requirements.ui_external_has_no_post(post):
  {==}

def Requirements.ui_external_has_no_auth(auth):
  {==}

def Requirements.ui_json_get_has_no_body():
  {==}

def Requirements.ui_html_get_has_no_body():
  {==}

def Requirements.ui_json_no_key_has_no_name():
  {==}

def Requirements.ui_html_no_key_has_no_name():
  {==}

def Requirements.home_empty_selection_cannot_zip():
  {==}
def Requirements.home_catalogue_has_no_file_action(reference):
  {==}
def Requirements.home_preparing_cannot_save():
  {==}
def Requirements.home_ready_can_save():
  {==}
def Requirements.home_stale_query_is_rejected():
  {==}
def Requirements.home_unconfirmed_audio_is_hidden():
  {==}
def Requirements.home_other_file_is_hidden():
  {==}

def Requirements.home_external_file_is_not_preselected(kind, preferred, images):
  {==}

def Requirements.home_other_file_is_not_preselected(preferred, images):
  {==}
