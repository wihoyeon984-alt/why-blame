import subprocess
import re


def get_repo_info():
    """?먭꺽 ??μ냼 URL?먯꽌 (?뚯쑀?? ??μ냼紐???異붿텧?⑸땲??"""
    res = subprocess.run(
        ["git", "config", "--get", "remote.origin.url"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    remote_url = res.stdout.strip()

    if not remote_url:
        return None

    m = re.search(r"github\.com[:/]([^/]+)/([^/.]+)", remote_url)

    if m:
        return m.group(1), m.group(2)

    return None


def get_current_code_lines(file_name, start_line, end_line):
    """吏?뺣맂 踰붿쐞???꾩옱 肄붾뱶 以꾨뱾??由ъ뒪?몃줈 ?쎌뼱?듬땲??"""
    try:
        with open(file_name, "r", encoding="utf-8") as f:
            lines = f.readlines()

        s = max(0, start_line - 1)
        e = min(len(lines), end_line)

        return [line.rstrip("\r\n") for line in lines[s:e]]

    except FileNotFoundError:
        print(f"?ㅻ쪟: ?뚯씪??李얠쓣 ???놁뒿?덈떎: {file_name}")
        return []

    except Exception as e:
        print(f"?ㅻ쪟: ?뚯씪 ?쎄린 ?ㅽ뙣: {e}")
        return []


def extract_git_history(file_name, start_line, end_line):
    """
    git log -L???ㅽ뻾??而ㅻ컠 ?뺣낫? ?ㅼ젣 肄붾뱶 蹂寃?Diff(-/+)瑜?異붿텧?⑸땲??

    以묒슂???먯튃:
    - commit message? diff瑜?遺꾨━?⑸땲??
    - Issue/PR 踰덊샇??commit message?먯꽌留?異붿텧?⑸땲??
    - diff ?대???'#123' 媛숈? 臾몄옄?댁? Issue/PR 李몄“濡?痍④툒?섏? ?딆뒿?덈떎.
    - ?꾩껜 commit SHA瑜?蹂댁〈?섏뿬 GitHub API??SHA 湲곕컲 PR 議고쉶???ъ슜?⑸땲??
    """

    cmd = [
        "git",
        "log",
        "-L",
        f"{start_line},{end_line}:{file_name}",
        "--no-merges",
        "--date=short",
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    if result.returncode != 0:
        print("??Git history 異붿쟻 ?ㅽ뙣:")
        print(result.stderr.strip())
        return []

    raw_log = result.stdout

    if not raw_log.strip():
        return []

    commits = []

    for block in raw_log.split("commit "):
        if not block.strip():
            continue

        lines = block.splitlines()

        if not lines:
            continue

        # ---------------------------------------------------------
        # Commit SHA
        # ---------------------------------------------------------
        full_hash = lines[0].strip()

        if not full_hash:
            full_hash = "Unknown"

        # ?붾㈃ 異쒕젰?대굹 吏㏃? ?앸퀎???ъ슜??7?먮━ SHA???④퍡 蹂닿?
        short_hash = full_hash[:7]

        # ---------------------------------------------------------
        # Commit metadata / Diff ?곸뿭 遺꾨━
        # ---------------------------------------------------------
        if "diff --git" in block:
            header_part, diff_part = block.split("diff --git", 1)
        else:
            header_part, diff_part = block, ""

        header_lines = header_part.splitlines()

        # ---------------------------------------------------------
        # ?좎쭨
        # ---------------------------------------------------------
        date_str = "Unknown"

        for line in header_lines:
            if line.startswith("Date:"):
                date_str = line.replace("Date:", "").strip()
                break

        # ---------------------------------------------------------
        # Commit message
        # ---------------------------------------------------------
        #
        # diff --git ?댁쟾??4移??ㅼ뿬?곌린留?commit message濡?痍④툒?⑸땲??
        #
        messages = [
            line.strip()
            for line in header_lines
            if line.startswith("    ")
        ]

        full_msg = " ".join(messages)

        # ---------------------------------------------------------
        # ?ㅼ젣 Diff
        # ---------------------------------------------------------
        #
        # + : 異붽???肄붾뱶
        # - : ??젣??肄붾뱶
        #
        # +++ / --- ?뚯씪 ?ㅻ뜑???쒖쇅?⑸땲??
        #
        diff_lines = []

        for line in diff_part.splitlines():

            if line.startswith("+") and not line.startswith("+++"):
                diff_lines.append("+ " + line[1:].strip())

            elif line.startswith("-") and not line.startswith("---"):
                diff_lines.append("- " + line[1:].strip())

        # ---------------------------------------------------------
        # Issue / PR 踰덊샇
        # ---------------------------------------------------------
        #
        # 諛섎뱶??commit message?먯꽌留?李얠뒿?덈떎.
        # ?곕씪??diff ?덉쓽 '#999'??Issue濡??몄떇?섏? ?딆뒿?덈떎.
        #
        numbers = re.findall(r"#(\d+)", full_msg)

        # ---------------------------------------------------------
        # Revert ?щ?
        # ---------------------------------------------------------
        is_revert = full_msg.strip().lower().startswith("revert")

        commits.append(
            {
                "hash": full_hash,
                "short_hash": short_hash,
                "date": date_str,
                "message": full_msg,
                "diff_lines": diff_lines,
                "refs": numbers,
                "is_revert": is_revert,
            }
        )

    return commits
