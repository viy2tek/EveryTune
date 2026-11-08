import Base
import ./model.bend as Model
import ./view.bend as View
import ./styles.bend as Styles
import ./quality.bend as Quality
import ./workflow.bend as Workflow

def transition(current: U32, event: U32) -> U32:
  Model.transition(current, event)
def accepts(active: U32, received: U32) -> U32:
  Model.accepts(active, received)
def can_zip(count: U32) -> U32:
  Model.can_zip(count)
def file_action(catalogue: U32, reference: U32) -> U32:
  Model.file_action(catalogue, reference)
def can_save(status: U32) -> U32:
  Model.can_save(status)
def toggle(open: U32) -> U32:
  Model.toggle(open)
def audio_result(available: U32) -> U32:
  Model.audio_result(available)
def allowed_file(kind: U32) -> U32:
  Model.allowed_file(kind)
def markup() -> String:
  View.markup()
def css() -> String:
  Styles.css() ++ Workflow.css()
def result_label(kind: U32) -> String:
  View.result_label(kind)
def summary(mode: U32, covers: U32) -> String:
  View.summary(mode, covers)
def quality(c: String, b: U32, s: U32, d: U32, n: U32, origin: U32) -> String:
  Quality.label(c, b, s, d, n, origin)
def quality_unknown() -> String:
  Quality.unknown()

def download_preferences_markup() -> String:
  Workflow.preferences()

def coverage_markup() -> String:
  Workflow.coverage()

def selection_markup() -> String:
  Workflow.selection()

def select_file(kind: U32, direct: U32, preferred: U32, images: U32) -> U32:
  Workflow.select_file(direct, kind, preferred, images)

def diagnostic_label(kind: U32) -> String:
  Workflow.diagnostic_label(kind)

def grouped_note() -> String:
  Workflow.grouped_note()

def footer_markup() -> String:
  Workflow.footer()

def license_page(contents: String) -> String:
  Workflow.license_page(contents)
