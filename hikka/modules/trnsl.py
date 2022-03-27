import os
import re

result = "{\n"

for mod in os.scandir("."):
    if not mod.path.endswith(".py") or mod.path.endswith("checker.py"):
        continue

    with open(mod.path, "r") as f:
        code = f.read()

    print(mod.path)
    try:
        strings = re.search("strings = {(.*?)    }", code, flags=re.S).group(1)
    except AttributeError:
        continue

    strs = [
        (
            re.search('"(.*?)": "(.*?)"', line).group(1),
            re.search('"(.*?)": "(.*?)"', line).group(2),
        )
        for line in strings.splitlines()
        if re.search('"(.*?)": "(.*?)"', line) is not None
    ]

    for st, tr in strs:
        if st == "name":
            continue

        result += f"    \"hikka.modules.{mod.path.split('/')[-1].split('.')[0]}.{st}\": \"{tr}\",\n"

    cmds = re.findall(r" +async def ([a-zA-Zа-яА-Я]*?)cmd\(.*?\).*?:.*?\"\"\"(.*?)\"\"\"", code, flags=re.S)

    for cmd, doc in cmds:
        doc = doc.replace('\n', '\\n')
        result += f"    \"hikka.modules.{mod.path.split('/')[-1].split('.')[0]}_cmd_doc_{cmd}\": \"{doc}\",\n"

    cls_ = re.search(r"@loader\.tds.*?class .*?Mod\(loader\.Module\):.*?\"\"\"(.*?)\"\"\"", code, flags=re.S)
    if cls_ is None:
        print("BRUH")
        continue

    result += f"    \"hikka.modules.{mod.path.split('/')[-1].split('.')[0]}_cls_doc\": \"{cls_.group(1)}\",\n"


result += "}"
print(result)
