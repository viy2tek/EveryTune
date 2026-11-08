import Base

# format: 0 external, 1 JSON, 2 HTML. Unknown values fail closed.
def mapping(format: U32) -> U32:
  match format:
    case 1: 1
    case 2: 1
    case _: 0

def post_body(format: U32, post: U32) -> U32:
  match format:
    case 1: post
    case 2: post
    case _: 0

def auth_name(format: U32, auth: U32) -> U32:
  match format:
    case 1: auth
    case 2: auth
    case _: 0
