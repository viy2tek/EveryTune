import Base

# phase: 0 initial, 1 searching, 2 results, 3 empty, 4 resolving,
# 5 choosing, 6 preparing, 7 ready, 8 failed. Events use the same codes.
def transition(current: U32, event: U32) -> U32:
  match event:
    case 0: 0
    case 1: 1
    case 2: 2
    case 3: 3
    case 4: 4
    case 5: 5
    case 6: 6
    case 7: 7
    case 8: 8
    case _: current

def accepts(active: U32, received: U32) -> U32:
  Bool.to_u32(U32.is_eq(active, received))

def can_zip(count: U32) -> U32:
  match count:
    case 0: 0
    case _: 1

def file_action(catalogue: U32, reference: U32) -> U32:
  match catalogue:
    case 1: 0
    case _: reference

def can_save(status: U32) -> U32:
  match status:
    case 7: 1
    case _: 0

def toggle(open: U32) -> U32:
  match open:
    case 0: 1
    case _: 0

def audio_result(available: U32) -> U32:
  match available:
    case 1: 1
    case _: 0

# 1 audio, 2 image; all other kinds are excluded.
def allowed_file(kind: U32) -> U32:
  match kind:
    case 1: 1
    case 2: 1
    case _: 0
