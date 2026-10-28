"""OPTIONAL step: run the extraction prompt from PROMPTS.md on proposals you place locally.

Put one text file per proposal in prototype/samples/ named A.txt, B.txt ...
(samples/ is git-ignored: the brief forbids committing proposal text.)
Needs ANTHROPIC_API_KEY (see .env.example). Not run in CI; the committed
extracted_facts.json is what score.py uses.

    python prototype/extract.py
Writes prototype/extracted_facts.generated.json
"""
import json, os, re, glob, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)


def env(name, default=None):
    if name in os.environ:
        return os.environ[name]
    path = os.path.join(HERE, ".env")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


def prompt_blocks():
    """Pull the fenced ```text blocks (system, user) and the schema ```json block out of PROMPTS.md."""
    md = open(os.path.join(ROOT, "PROMPTS.md"), encoding="utf-8").read()
    section = md.split("## 2.")[0]
    texts = re.findall(r"```text\n(.*?)```", section, re.S)
    schema = re.findall(r"```json\n(.*?)```", section, re.S)[0]
    return texts[0], texts[1], schema


def norm(s):
    return re.sub(r"\s+", " ", s).strip().lower()


def call_model(system, user):
    body = json.dumps({"model": env("MODEL", "claude-sonnet-5-5"), "max_tokens": 1500, "temperature": 0,
                       "system": system, "messages": [{"role": "user", "content": user}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", body, {
        "content-type": "application/json", "x-api-key": env("ANTHROPIC_API_KEY"),
        "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    return "".join(b.get("text", "") for b in data["content"])


def main():
    crit = json.load(open(os.path.join(HERE, "criteria.json"), encoding="utf-8"))
    ref = crit["project"]["reference_date"]
    sys_t, user_t, schema = prompt_blocks()
    system = sys_t.replace("{reference_date}", ref).replace("{schema_json}", schema)
    out = {}
    for path in sorted(glob.glob(os.path.join(HERE, "samples", "*.txt"))):
        letter = os.path.splitext(os.path.basename(path))[0]
        text = open(path, encoding="utf-8").read()
        user = (user_t.replace("{category_name}", crit["category"]).replace("{reference_date}", ref)
                .replace("{proposal_letter}", letter).replace("{proposal_text}", text))
        raw = call_model(system, user)
        data = json.loads(raw[raw.index("{"): raw.rindex("}") + 1])
        fields, evidence, unverified = data["fields"], data.get("evidence", {}), []
        # RULE-BASED VALIDATION: every non-null value needs a quote that really appears in the text
        for k, v in list(fields.items()):
            if v is None or k == "installs_window_uncertain":
                continue
            q = evidence.get(k)
            if not q or norm(q) not in norm(text):
                fields[k] = None
                unverified.append(k)
        fields["instruction_like_text"] = data.get("instruction_like_text", [])
        # second, independent rule-based scan for injection phrases
        if re.search(r"(automated review|ai system|rank (it )?first|full marks|pre-?approved)", text, re.I) \
                and not fields["instruction_like_text"]:
            fields["instruction_like_text"] = ["<detected by regex scan>"]
        fields["_unverified_fields"] = unverified
        out[letter] = fields
    dest = os.path.join(HERE, "extracted_facts.generated.json")
    json.dump(out, open(dest, "w", encoding="utf-8"), indent=2)
    print("wrote", dest)


if __name__ == "__main__":
    main()
