#!/usr/bin/env python3
import os

from flask import Flask, redirect, render_template_string, request
import pymysql
from google.cloud import secretmanager

app = Flask(__name__)
APP_BUILD = "ui-v4"

PROJECT_ID = os.environ["GCP_PROJECT"]

def get_secret(secret_id, version="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version}"
    return client.access_secret_version(request={"name": name}).payload.data.decode("utf-8")

DB_HOST = os.environ.get("DB_HOST", "10.30.0.3")
DB_NAME = os.environ.get("DB_NAME", "lab")
DB_USER = os.environ.get("DB_USER", "progress_app")
DB_PASSWORD = get_secret("db-password")
DB_SSL_CA = os.environ.get("DB_SSL_CA", "/opt/progress-app/server-ca.pem")

BASE_STYLE = """
:root {
  --bg: #f3efe6;
  --paper: #fffcf7;
  --ink: #1f1b16;
  --muted: #6f675c;
  --line: #e4dccf;
  --teal: #0f5c4c;
  --teal-soft: #e4f0eb;
  --amber: #9a6700;
  --amber-soft: #f8eedc;
  --draft: #7a746b;
  --draft-soft: #eeeae3;
}
* { box-sizing: border-box; }
body {
  margin: 0;
  color: var(--ink);
  background:
    radial-gradient(ellipse at top, #fffaf1 0%, var(--bg) 55%);
  font-family: "PingFang TC", "Noto Sans TC", "Hiragino Sans GB",
    "Microsoft JhengHei", sans-serif;
  line-height: 1.65;
}
.wrap { max-width: 44rem; margin: 0 auto; padding: 2rem 1.25rem 4rem; }
.site-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 1rem;
  padding-bottom: 1.25rem;
  border-bottom: 2px solid var(--ink);
  margin-bottom: 1.75rem;
}
.eyebrow {
  margin: 0 0 0.2rem;
  font-size: 0.75rem;
  letter-spacing: 0.16em;
  text-transform: uppercase;
  color: var(--teal);
  font-weight: 700;
}
h1 { margin: 0; font-size: 1.85rem; letter-spacing: -0.02em; }
.lede { margin: 0.35rem 0 0; color: var(--muted); font-size: 0.95rem; }
.nav { display: flex; align-items: center; gap: 0.75rem; flex-shrink: 0; }
.nav a {
  color: var(--ink);
  text-decoration: none;
  font-size: 0.9rem;
  border-bottom: 1px solid var(--line);
}
.nav a:hover { border-bottom-color: var(--ink); }
.btn {
  display: inline-block;
  text-decoration: none;
  border-radius: 999px;
  padding: 0.55rem 1.05rem;
  background: var(--teal);
  color: #fff !important;
  font-weight: 700;
  font-size: 0.9rem;
  border: 0;
}
.btn:hover { filter: brightness(1.08); }
.admin-mark {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  border-radius: 999px;
  background: var(--ink);
  color: var(--paper);
  font-size: 0.72rem;
  letter-spacing: 0.08em;
}
.timeline { list-style: none; margin: 0; padding: 0; }
.item {
  position: relative;
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1.1rem 1.2rem 1.15rem 1.35rem;
  margin: 0 0 0.9rem;
  box-shadow: 0 8px 24px rgba(31, 27, 22, 0.04);
}
.item h2 { margin: 0.15rem 0 0.35rem; font-size: 1.12rem; line-height: 1.4; }
.item p { margin: 0.4rem 0 0; color: #3d3832; }
.meta { display: flex; flex-wrap: wrap; gap: 0.45rem 0.7rem; align-items: center; }
.badge {
  display: inline-block;
  padding: 0.12rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}
.badge.done { background: var(--teal-soft); color: var(--teal); }
.badge.wip { background: var(--amber-soft); color: var(--amber); }
.badge.note { background: var(--draft-soft); color: var(--draft); }
.badge.live { background: var(--teal-soft); color: var(--teal); }
.badge.draft { background: var(--draft-soft); color: var(--draft); }
time { color: var(--muted); font-size: 0.82rem; }
.empty {
  padding: 2.5rem 1rem;
  text-align: center;
  color: var(--muted);
  border: 1px dashed var(--line);
  border-radius: 14px;
  background: rgba(255,252,247,0.6);
}
.empty .btn { margin-top: 0.9rem; }
.panel {
  background: var(--paper);
  border: 1px solid var(--line);
  border-radius: 14px;
  padding: 1.2rem;
  margin-bottom: 1.5rem;
}
.panel h2 { margin: 0 0 0.9rem; font-size: 1rem; }
label { display: block; margin: 0.85rem 0 0.3rem; font-size: 0.88rem; font-weight: 700; }
input[type=text], textarea {
  width: 100%;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 0.65rem 0.75rem;
  font: inherit;
  color: var(--ink);
  background: #fff;
}
input[type=text]:focus, textarea:focus {
  outline: 2px solid var(--teal);
  outline-offset: 1px;
  border-color: var(--teal);
}
textarea { min-height: 7rem; resize: vertical; }
.check {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-top: 1rem;
  font-weight: 500;
}
.submit {
  margin-top: 1.1rem;
  border: 0;
  border-radius: 999px;
  padding: 0.65rem 1.2rem;
  background: var(--teal);
  color: #fff;
  font: inherit;
  font-weight: 700;
  cursor: pointer;
}
.submit:hover { filter: brightness(1.08); }
.actions { display: flex; flex-wrap: wrap; gap: 0.35rem; }
.btn-ghost {
  margin: 0;
  background: #fff;
  color: var(--ink);
  border: 1px solid var(--line);
  padding: 0.28rem 0.65rem;
  border-radius: 999px;
  font: inherit;
  font-size: 0.75rem;
  font-weight: 600;
  cursor: pointer;
}
.btn-danger { color: #8a2b2b; border-color: #e2c8c8; }
a.btn-ghost { display: inline-block; text-decoration: none; line-height: 1.45; }
.flash {
  background: var(--teal-soft);
  color: var(--teal);
  border-radius: 10px;
  padding: 0.7rem 0.9rem;
  margin-bottom: 1rem;
  font-weight: 600;
}
.rows { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
.rows th, .rows td {
  text-align: left;
  padding: 0.7rem 0.35rem;
  border-bottom: 1px solid var(--line);
  vertical-align: top;
}
.rows th { color: var(--muted); font-size: 0.75rem; font-weight: 700; letter-spacing: 0.06em; }
"""

LIST_HTML = """
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>工作進度</title>
  <style>{{ base_style | safe }}</style>
</head>
<body>
  <div class="wrap">
    <header class="site-header">
      <div>
        <p class="eyebrow">Lab progress</p>
        <h1>工作進度</h1>
      </div>
      <nav class="nav"><a class="btn" href="/admin">發布進度</a></nav>
    </header>
    {% if updates %}
      <ol class="timeline">
        {% for item in updates %}
          <li class="item">
            <div class="meta">
              <span class="badge {{ item.kind }}">{{ item.kind_label }}</span>
              <time>{{ item.created_label }}</time>
            </div>
            <h2>{{ item.title }}</h2>
            {% if item.body %}<p>{{ item.body }}</p>{% endif %}
          </li>
        {% endfor %}
      </ol>
    {% else %}
      <div class="empty">
        <p>目前沒有已發布的進度。</p>
        <a class="btn" href="/admin">發布第一則</a>
      </div>
    {% endif %}
  </div>
</body>
</html>
"""

ADMIN_HTML = """
<!doctype html>
<html lang="zh-Hant">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>發布進度</title>
  <style>{{ base_style }}</style>
</head>
<body>
  <div class="wrap">
    <header class="site-header">
      <div>
        <p class="eyebrow">Internal</p>
        <h1>發布進度 <span class="admin-mark">ADMIN</span></h1>
        <p class="lede">寫一則進度，勾選後會出現在公開頁。</p>
      </div>
      <nav class="nav"><a href="/">看公開頁</a></nav>
    </header>
    {% if saved == "1" %}
      <div class="flash">已發布，公開頁可以看到這一則。</div>
    {% elif saved == "0" %}
      <div class="flash">已存成草稿，公開頁不會顯示。</div>
    {% elif saved == "edit" %}
      <div class="flash">已儲存修改。</div>
    {% elif saved == "del" %}
      <div class="flash">已刪除這一則。</div>
    {% endif %}
    <section class="panel">
      <h2>{{ "修改這一則" if editing else "新增一則" }}</h2>
      <form method="post">
        {% if editing %}
          <input type="hidden" name="action" value="update">
          <input type="hidden" name="id" value="{{ editing.id }}">
        {% else %}
          <input type="hidden" name="action" value="create">
        {% endif %}
        <label for="title">標題</label>
        <input id="title" name="title" type="text" required maxlength="200"
               placeholder="例如：已完成：開放 Internet 訪問"
               value="{{ editing.title if editing else '' }}">
        <label for="body">說明（可空）</label>
        <textarea id="body" name="body" placeholder="兩三句即可，不必寫成長報告。">{{ editing.body if editing and editing.body else '' }}</textarea>
        <label class="check">
          <input type="checkbox" name="published" value="1"
                 {% if not editing or editing.published %}checked{% endif %}>
          發布到公開頁
        </label>
        <button class="submit" type="submit">{{ "儲存修改" if editing else "送出" }}</button>
        {% if editing %}
          <p class="lede"><a href="/admin">取消修改</a></p>
        {% endif %}
      </form>
    </section>
    <section class="panel">
      <h2>目前紀錄</h2>
      <table class="rows">
        <thead>
          <tr><th>狀態</th><th>標題</th><th>時間</th><th>操作</th></tr>
        </thead>
        <tbody>
          {% for item in updates %}
            <tr>
              <td>
                <span class="badge {{ 'live' if item.published else 'draft' }}">
                  {{ "已發布" if item.published else "草稿" }}
                </span>
              </td>
              <td>{{ item.title }}</td>
              <td><time>{{ item.created_label }}</time></td>
              <td>
                <div class="actions">
                  <a class="btn-ghost" href="/admin?edit={{ item.id }}">修改</a>
                  <form method="post" onsubmit="return confirm('確定刪除這一則？');">
                    <input type="hidden" name="action" value="delete">
                    <input type="hidden" name="id" value="{{ item.id }}">
                    <button class="btn-ghost btn-danger" type="submit">刪除</button>
                  </form>
                </div>
              </td>
            </tr>
          {% endfor %}
        </tbody>
      </table>
    </section>
  </div>
</body>
</html>
"""


def decorate(rows):
    items = []
    for row in rows:
        item = dict(row)
        ts = item.get("created_at")
        item["created_label"] = ts.strftime("%Y-%m-%d %H:%M") if ts else ""
        title = item.get("title") or ""
        if title.startswith("已完成"):
            item["kind"] = "done"
            item["kind_label"] = "已完成"
        elif title.startswith("進行中"):
            item["kind"] = "wip"
            item["kind_label"] = "進行中"
        else:
            item["kind"] = "note"
            item["kind_label"] = "公告"
        items.append(item)
    return items


def get_conn():
    if not os.path.isfile(DB_SSL_CA):
        raise FileNotFoundError(
            f"找不到 Cloud SQL CA：{DB_SSL_CA}。請把 server-ca.pem 放到這個路徑，或 export DB_SSL_CA"
        )

    # 第一次報 IP mismatch，代表 CA 已載入且鏈結通過。
    # 那時只差沒關 hostname；不要再用 ssl_verify_cert=True（Python 3.13 會丟 CA）。
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
        ssl={"ca": DB_SSL_CA, "check_hostname": False},
    )


@app.get("/health")
def health():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT 1")
        return "ok\n", 200, {"Content-Type": "text/plain; charset=utf-8"}
    finally:
        conn.close()


@app.get("/")
def index():
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT title, body, created_at
                FROM updates
                WHERE published = 1
                ORDER BY created_at DESC, id DESC
                """
            )
            updates = decorate(cur.fetchall())
    finally:
        conn.close()
    return render_template_string(LIST_HTML, updates=updates, base_style=BASE_STYLE)


@app.route("/admin", methods=["GET", "POST"])
def admin():
    conn = get_conn()
    try:
        if request.method == "POST":
            action = request.form.get("action") or "create"
            try:
                item_id = int(request.form.get("id") or 0)
            except ValueError:
                item_id = 0
            if action == "delete" and item_id > 0:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM updates WHERE id = %s", (item_id,))
                conn.commit()
                return redirect("/admin?saved=del")
            if action in ("create", "update"):
                title = (request.form.get("title") or "").strip()
                body = (request.form.get("body") or "").strip()
                published = 1 if request.form.get("published") == "1" else 0
                if title and action == "update" and item_id > 0:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE updates
                            SET title = %s, body = %s, published = %s
                            WHERE id = %s
                            """,
                            (title, body, published, item_id),
                        )
                    conn.commit()
                    return redirect("/admin?saved=edit")
                if title and action == "create":
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO updates (title, body, published)
                            VALUES (%s, %s, %s)
                            """,
                            (title, body, published),
                        )
                    conn.commit()
                    return redirect("/admin?saved=" + ("1" if published else "0"))

        editing = None
        try:
            edit_id = int(request.args.get("edit") or 0)
        except ValueError:
            edit_id = 0
        if edit_id > 0:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, title, body, published
                    FROM updates
                    WHERE id = %s
                    """,
                    (edit_id,),
                )
                editing = cur.fetchone()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, title, published, created_at
                FROM updates
                ORDER BY created_at DESC, id DESC
                """
            )
            updates = decorate(cur.fetchall())
    finally:
        conn.close()
    return render_template_string(
        ADMIN_HTML,
        updates=updates,
        editing=editing,
        base_style=BASE_STYLE,
        saved=request.args.get("saved"),
    )


if __name__ == "__main__":
    # 本機測試用；VM 上由 gunicorn 啟動，不會執行這段

    print(f"progress_app {APP_BUILD}")
    print(f"CA={DB_SSL_CA} exists={os.path.isfile(DB_SSL_CA)}")
    app.run(host="0.0.0.0", port=8080)
