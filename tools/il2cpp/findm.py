import ijson, sys

SCRIPT = "out/script.json"
NEEDLES = sys.argv[1:]

cur = None
with open(SCRIPT, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if prefix == "ScriptMethod.item.Address":
            cur = value
        elif prefix == "ScriptMethod.item.Name":
            if any(nd in value for nd in NEEDLES):
                print(f"0x{cur:x}  {value}")
        elif prefix.startswith("ScriptString"):
            break
