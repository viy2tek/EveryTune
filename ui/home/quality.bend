import Base

def codec(value: String) -> String:
  match value:
    case SNil{}: ""
    case SCon{h, t}: SCon{h, t} ++ " · "

def bitrate_value(value: U32, remainder: U32) -> String:
  match remainder:
    case 0: U32.show((value / 1000 : U32)) ++ " kbps · "
    case _: U32.show(value) ++ " bit/s · "

def bitrate(+value: U32) -> String:
  match value:
    case 0: ""
    case _: bitrate_value(value, (value % 1000 : U32))

def sample_rate(value: U32) -> String:
  match value:
    case 0: ""
    case _: U32.show(value) ++ " Hz · "

def depth(value: U32) -> String:
  match value:
    case 0: ""
    case _: U32.show(value) ++ " bits · "

def channels(value: U32) -> String:
  match value:
    case 0: ""
    case 1: "mono · "
    case 2: "estéreo · "
    case _: U32.show(value) ++ " canais · "

def basis(value: U32) -> String:
  match value:
    case 1: "lido no arquivo"
    case 2: "lido nos cabeçalhos"
    case _: "informado pela fonte"

def label(c: String, b: U32, s: U32, d: U32, n: U32, origin: U32) -> String:
  codec(c) ++ bitrate(b) ++ sample_rate(s) ++ depth(d) ++ channels(n) ++ basis(origin)

def unknown() -> String:
  "Dados técnicos não identificados"
