from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse
from pathlib import Path
from email.parser import BytesParser
from email.policy import default
from html import escape
import json
import mimetypes
import re
import uuid


BASE_DIR = Path(__file__).parent
UPLOADS_DIR = BASE_DIR / "uploads"
TEACHERS_FILE = BASE_DIR / "teachers.json"


PAGE = r'''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Стимул — онлайн-школа</title>
  <script src="https://unpkg.com/htmx.org@2.0.4"></script>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&family=Playfair+Display:ital,wght@0,600;0,700;1,600&display=swap" rel="stylesheet">
  <style>
    :root { --ink:#202020; --muted:#747474; --cream:#fff; --mint:#f4f4f1; --lime:#dce864; --coral:#ee8875; --white:#fff; }
    * { box-sizing:border-box; }
    body { margin:0; font-family:Manrope,Arial,sans-serif; background:var(--cream); color:var(--ink); }
    .wrap { max-width:1180px; margin:auto; padding:0 28px; }
    .site-header { background:#bfe8f8; }
    header { padding:24px 0; display:flex; align-items:center; justify-content:space-between; gap:24px; }
    .logo { font-size:23px; font-weight:800; letter-spacing:.03em; text-decoration:none; color:var(--ink); display:flex; align-items:center; background:#fff; border-radius:14px; padding:15px 18px; }
    nav { display:flex; gap:24px; }
    nav a { text-decoration:none; color:var(--ink); font-size:16px; font-weight:700; }
    .header-contacts { display:flex; flex-direction:column; gap:4px; }
    .header-contacts a { color:var(--ink); text-decoration:none; font-size:15px; font-weight:800; white-space:nowrap; }
    .header-contacts a:hover { text-decoration:underline; }
    .header-link { border-bottom:1px solid var(--ink); padding-bottom:3px; font-size:15px; font-weight:700; white-space:nowrap; }
    .application-banner { margin:36px 0 82px; background:var(--mint); border-radius:15px; padding:29px 34px; display:flex; align-items:center; justify-content:space-between; gap:30px; }
    .application-banner h1 { font-family:Manrope,Arial,sans-serif; font-size:22px; letter-spacing:-.03em; line-height:1.25; margin:0; font-weight:800; }
    .application-banner p { color:var(--muted); font-size:13px; margin:5px 0 0; }
    .hero { padding:76px 0 64px; display:grid; grid-template-columns:1.05fr .95fr; align-items:center; gap:45px; }
    .hero-title { display:flex; align-items:center; gap:26px; margin-bottom:27px; }
    .hero-logo { width:208px; height:208px; flex:0 0 auto; object-fit:contain; }
    .hero h1 { font-family:Manrope,Arial,sans-serif; font-size:clamp(29px,3.4vw,42px); line-height:1.08; letter-spacing:-.045em; margin:0; font-weight:800; }
    .hero-text { color:var(--muted); max-width:490px; line-height:1.65; font-size:17px; margin:0; }
    .hero-actions { display:flex; align-items:center; gap:23px; margin-top:33px; }
    .primary-btn { display:inline-block; text-decoration:none; border:0; border-radius:10px; background:var(--ink); color:#fff; padding:16px 21px; font:700 14px Manrope,Arial,sans-serif; cursor:pointer; }
    .hero-note { color:var(--muted); font-size:12px; max-width:150px; }
    .hero-art { min-height:382px; background:#bfe8f8; border-radius:25px; padding:46px; display:flex; align-items:center; }
    .lead-form { width:100%; }.lead-form h2 { font-size:29px; margin-bottom:9px; }.lead-form p{margin:0 0 23px;color:#426271;font-size:13px;line-height:1.5}.lead-form input{display:block;width:100%;border:1px solid rgba(32,32,32,.18);background:#fff;border-radius:8px;padding:14px 13px;margin-top:10px;font:14px Manrope,Arial,sans-serif;outline:0}.lead-form button{margin-top:14px;width:100%;border:0;border-radius:8px;background:#202020;color:#fff;padding:15px;font:700 14px Manrope,Arial,sans-serif;cursor:pointer}.lead-form button:disabled{opacity:.65;cursor:wait}.lead-success{font-size:17px;font-weight:700;line-height:1.5}.lead-status{min-height:20px;margin:12px 0 0!important;color:#7a3028!important;font-weight:700}
    .metrics { background:#202020; color:#fff; margin:0 0 96px; }
    .metric-grid { min-height:150px; display:grid; grid-template-columns:repeat(4,1fr); align-items:center; }
    .metric { padding:15px 27px; border-left:1px solid #444; }.metric:first-child{border-left:0;padding-left:0}.metric b{display:block;font-size:31px;letter-spacing:-.05em;color:#dce864}.metric span{font-size:12px;line-height:1.45;display:block;margin-top:6px;color:#ddd}
    .features { padding:0 0 105px; }.features-intro { text-align:center; max-width:690px; margin:0 auto 45px; }.features-intro h2{margin-bottom:0}
    .feature-grid { display:grid; grid-template-columns:repeat(3,1fr); gap:15px; }.feature { padding:28px; border-radius:16px; background:#f4f4f1; min-height:220px; }.feature:nth-child(2){background:#eaf7fd}.feature:nth-child(3){background:#f9f0ec}.feature-icon{width:42px;height:42px;border-radius:12px;background:#fff;display:grid;place-items:center;font-size:20px;margin-bottom:38px}.feature h3{font-size:17px;margin:0 0 10px}.feature p{font-size:13px;color:var(--muted);line-height:1.55;margin:0}
    .study { background:#bfe8f8; padding:72px 0; margin:0 0 90px; }.study-inner{display:flex;justify-content:space-between;align-items:end;gap:35px}.study h2{max-width:510px}.study p{max-width:370px;margin:0;color:#426271;line-height:1.6;font-size:14px}
    .hero-copy { max-width:575px; padding-left:28px; position:relative; z-index:2; }
    .eyebrow { font-size:12px; font-weight:800; letter-spacing:.13em; text-transform:uppercase; color:#497350; margin:0 0 21px; }
    h1 { font-family:"Playfair Display",Georgia,serif; font-size:67px; line-height:1.04; letter-spacing:-.045em; margin:0 0 27px; font-weight:600; }
    h1 em { color:#e46f5c; font-style:italic; }
    .hero p { margin:0; color:#4f645a; font-size:17px; line-height:1.7; max-width:440px; }
    .cta { background:var(--ink); color:white; border:0; border-radius:100px; padding:17px 25px; font:700 14px Manrope,sans-serif; margin-top:34px; cursor:pointer; transition:.2s transform; }
    .cta:hover { transform:translateY(-2px); }
    .hero-image { position:absolute; right:0; bottom:0; width:48%; height:100%; object-fit:cover; object-position:center; mix-blend-mode:multiply; }
    .circle { position:absolute; border-radius:50%; }
    .circle-one { width:280px; height:280px; background:var(--lime); bottom:-105px; left:39%; }
    .circle-two { width:80px; height:80px; border:1px solid #7fa379; top:51px; right:43%; }
    .stats { position:absolute; z-index:3; right:56px; bottom:38px; display:flex; background:rgba(255,254,250,.86); padding:16px 22px; border-radius:16px; gap:26px; backdrop-filter:blur(8px); }
    .stat + .stat { border-left:1px solid #c8d9c5; padding-left:26px; }
    .stat b { display:block; font-size:21px; } .stat span { font-size:11px; color:var(--muted); }
    .teachers { padding:0 0 100px; }
    .section-head { display:flex; align-items:center; justify-content:center; gap:20px; margin-bottom:45px; text-align:center; }
    h2 { font-family:Manrope,Arial,sans-serif; font-weight:800; font-size:42px; line-height:1.1; letter-spacing:-.04em; margin:0; }
    .section-head p { max-width:330px; margin:0; color:var(--muted); font-size:14px; line-height:1.65; }
    .teacher-grid { display:grid; grid-template-columns:1fr; gap:24px; }
    .teacher { display:grid; grid-template-columns:330px 1fr; overflow:hidden; background:#fff; border:1px solid #e3e5e1; border-radius:20px; box-shadow:0 8px 30px rgba(32,32,32,.05); transition:transform .25s,box-shadow .25s; }
    .teacher:hover { transform:translateY(-5px); box-shadow:0 18px 42px rgba(32,32,32,.1); }
    .photo { height:100%; min-height:330px; overflow:hidden; background:#eaf7fd; }
    .photo img { width:100%; height:100%; display:block; object-fit:cover; filter:saturate(.9); transition:transform .45s; }
    .teacher:hover .photo img { transform:scale(1.03); }
    .teacher-info { display:flex; align-items:flex-start; justify-content:center; flex-direction:column; padding:38px 44px; }
    .teacher h3 { margin:0 0 12px; color:#202020; font-size:25px; line-height:1.2; letter-spacing:-.035em; }
    .subject { display:inline-flex; align-items:center; border-radius:50px; padding:8px 12px; background:#bfe8f8; color:#202020; font-size:15px; font-weight:800; }
    .teacher p { width:100%; margin:22px 0 0; padding-top:20px; border-top:1px solid #e3e5e1; color:#202020; font-size:18px; line-height:1.75; }
    .empty-teachers { color:var(--muted); font-size:15px; }
    .join { background:var(--coral); padding:66px 72px; border-radius:25px; color:#fffaf6; display:flex; justify-content:space-between; align-items:center; gap:45px; margin-bottom:52px; }
    .join h2 { font-size:39px; max-width:510px; } .join p { margin:12px 0 0; font-size:14px; line-height:1.55; }
    .form { background:#fff; border-radius:10px; padding:5px; display:flex; width:390px; }
    .form input { border:0; outline:0; padding:0 13px; width:100%; font:13px Manrope,sans-serif; background:transparent; }
    .form button { border:0; border-radius:10px; background:var(--ink); color:#fff; padding:13px 16px; white-space:nowrap; font:700 12px Manrope,sans-serif; cursor:pointer; }
    footer { padding:0 0 38px; display:flex; justify-content:space-between; color:var(--muted); font-size:12px; }
    .success { font-size:13px; font-weight:700; margin-top:11px; }
    @media (max-width: 960px) { nav{display:none} }
    @media (max-width: 760px) { .wrap{padding:0 16px} header{padding:14px 0;display:flex;flex-wrap:wrap;gap:12px}.logo{font-size:19px}.header-contacts{order:3;width:100%;flex-direction:row;justify-content:space-between}.header-contacts a{font-size:clamp(12px,3.6vw,14px)}.header-link{font-size:13px}.hero{padding:45px 0;grid-template-columns:1fr;gap:28px}.hero-art{min-height:280px}.hero-logo{width:132px;height:132px;left:39px;top:68px}.hero-art:after{width:85px;height:85px;border-width:13px;right:32px;top:30px}.metrics{margin-bottom:62px}.metric-grid{grid-template-columns:1fr 1fr;padding:15px 0}.metric,.metric:first-child{padding:18px;border-left:0}.features{padding-bottom:68px}.feature-grid{grid-template-columns:1fr}.feature{min-height:0}.feature-icon{margin-bottom:25px}.study{padding:48px 0;margin-bottom:60px}.study-inner{display:block}.study p{margin-top:18px}.application-banner{margin:22px 0 54px;padding:23px;display:block}.application-banner .form{margin-top:19px}.section-head{align-items:start;flex-direction:column}.teacher{grid-template-columns:1fr}.photo{height:330px;min-height:0}.teacher-info{padding:27px 24px}.teacher p{font-size:17px}.form{width:100%}footer{gap:12px;flex-direction:column} }
    @media (max-width: 760px) { .hero-copy{padding-left:8px}.hero-title{align-items:flex-start;flex-direction:column;gap:16px}.hero-logo{width:176px;height:176px}.hero h1{font-size:34px} }
  </style>
</head>
<body>
  <div class="site-header"><div class="wrap"><header>
    <a class="logo" href="#top">СТИМУЛ</a>
    <nav><a href="#features">О занятиях</a><a href="#teachers">Преподаватели</a><a href="#format">Формат</a></nav>
    <div class="header-contacts"><a href="tel:+79055188365">+7 905 518-83-65</a><a href="tel:+79685742629">+7 968 574-26-29</a></div>
    <a class="header-link" href="#application">Оставить заявку</a>
  </header></div></div>
  <main id="top">
    <section class="hero wrap"><div class="hero-copy"><div class="hero-title"><img class="hero-logo" src="/diploma.png" alt="Логотип школы Стимул"><h1>Онлайн-школа для детей и подростков</h1></div><p class="hero-text">Помогаем уверенно разбираться в школьных предметах, готовиться к экзаменам и открывать новые возможности.</p></div><div class="hero-art" id="application"><div id="application-result" style="width:100%"><form class="lead-form" id="application-form" action="https://api.web3forms.com/submit" method="POST"><h2>Оставить заявку</h2><p>Познакомимся и подберём удобное время для занятия.</p><input type="hidden" name="access_key" value="6f7c5b18-8651-4a1c-83ad-89c42d1ad9d4"><input type="hidden" name="subject" value="Новая заявка с сайта «Стимул»"><input type="hidden" name="from_name" value="Сайт школы «Стимул»"><input type="checkbox" name="botcheck" tabindex="-1" autocomplete="off" style="display:none"><input required name="name" placeholder="Ваше имя" aria-label="Ваше имя"><input required name="phone" type="tel" placeholder="Телефон" aria-label="Телефон"><input required name="email" type="email" placeholder="Электронная почта" aria-label="Электронная почта"><button type="submit">Отправить заявку</button><p class="lead-status" id="application-status" aria-live="polite"></p></form></div></div></section>
    <section class="teachers wrap" id="teachers">
      <div class="section-head"><h2>Наши преподаватели</h2></div>
      <div class="teacher-grid">{{TEACHERS}}</div>
    </section>
    <section class="features wrap" id="features"><div class="features-intro"><h2>Как проходят занятия</h2></div><div class="feature-grid"><article class="feature"><div class="feature-icon">◉</div><h3>Живой диалог</h3><p>Разбираем темы вместе, задаём вопросы и сразу находим ответы.</p></article><article class="feature"><div class="feature-icon">✦</div><h3>Понятная практика</h3><p>Закрепляем знания на задачах, которые помогают увидеть результат.</p></article><article class="feature"><div class="feature-icon">✓</div><h3>Своя траектория</h3><p>Подбираем программу под уровень, цель и темп ученика.</p></article></div></section>
    <section class="study" id="format"><div class="wrap study-inner"><h2>Учимся там, где удобно</h2><p>Индивидуальные онлайн-занятия с преподавателем. Всё нужное для урока уже есть: видеосвязь, интерактивная доска и материалы.</p></div></section>
  </main>
  <script>
    const applicationForm = document.querySelector("#application-form");
    applicationForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      const button = applicationForm.querySelector("button");
      const status = document.querySelector("#application-status");
      const originalLabel = button.textContent;
      button.disabled = true;
      button.textContent = "Отправляем…";
      status.textContent = "";

      try {
        const response = await fetch(applicationForm.action, {
          method: "POST",
          body: new FormData(applicationForm)
        });
        const result = await response.json();
        if (!response.ok || !result.success) throw new Error("Web3Forms rejected submission");
        document.querySelector("#application-result").innerHTML =
          '<p class="lead-success">Спасибо! Заявка отправлена, скоро свяжемся с вами.</p>';
      } catch (error) {
        status.textContent = "Не удалось отправить заявку. Пожалуйста, попробуйте немного позже.";
        button.disabled = false;
        button.textContent = originalLabel;
      }
    });
  </script>
</body></html>'''


def load_teachers():
    if not TEACHERS_FILE.exists():
        return []
    try:
        teachers = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(teachers, list):
        return []


    changed = False
    for teacher in teachers:
        if "id" not in teacher:
            teacher["id"] = uuid.uuid4().hex
            changed = True
    if changed:
        TEACHERS_FILE.write_text(json.dumps(teachers, ensure_ascii=False, indent=2), encoding="utf-8")
    return teachers


def render_admin_teacher(teacher):
    return f'''<article class="teacher-card">
      <img src="{escape(teacher['photo'])}" alt="{escape(teacher['name'])}">
      <div class="teacher-card-info"><h2>{escape(teacher['name'])}</h2><span>{escape(teacher['subject'])}</span><p>{escape(teacher['bio'])}</p><button class="delete" hx-delete="/teachers/{escape(teacher['id'])}" hx-target="#teacher-list" hx-swap="innerHTML" hx-confirm="Удалить преподавателя?">Удалить</button></div>
    </article>'''


def render_public_teachers():
    teachers = load_teachers()
    if not teachers:
        return '<p class="empty-teachers">Список преподавателей скоро появится здесь.</p>'
    return "".join(f'''<article class="teacher">
      <div class="photo"><img src="{escape(teacher['photo'])}" alt="{escape(teacher['name'])}"></div>
      <div class="teacher-info"><h3>{escape(teacher['name'])}</h3><span class="subject">{escape(teacher['subject'])}</span><p>{escape(teacher['bio'])}</p></div>
    </article>''' for teacher in teachers)


def admin_page():
    teachers = load_teachers()
    cards = "".join(render_admin_teacher(teacher) for teacher in teachers)
    empty = "" if cards else '<p class="empty">Пока не добавлено ни одного преподавателя.</p>'
    return f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Стимул — управление</title><link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap" rel="stylesheet"><script src="https://unpkg.com/htmx.org@2.0.4"></script>
    <style>
      :root{{--ink:#202020;--muted:#747474;--sky:#bfe8f8;--paper:#f4f4f1;--white:#fff;--lime:#dce864;--danger:#b54e42;--line:#dfe1dd}}
      *{{box-sizing:border-box}}html{{scroll-behavior:smooth}}body{{margin:0;background:#fff;color:var(--ink);font:15px Manrope,Arial,sans-serif}}a{{color:inherit}}
      .admin-wrap{{width:min(1060px,calc(100% - 48px));margin:0 auto}}.admin-topbar{{background:var(--sky)}}.admin-header{{height:92px;display:flex;align-items:center;justify-content:space-between;gap:24px}}
      .brand{{display:flex;align-items:center;padding:15px 18px;border-radius:14px;background:#fff;text-decoration:none;font-size:20px;font-weight:800;letter-spacing:.03em}}
      .site-link{{padding-bottom:3px;border-bottom:1px solid var(--ink);text-decoration:none;font-size:14px;font-weight:700}}
      main{{padding:68px 0 100px}}h1{{margin:0;font-size:clamp(44px,6vw,66px);line-height:1;letter-spacing:-.055em}}
      .editor{{margin:48px 0 82px;padding:37px;border-radius:24px;background:var(--sky)}}.editor-head{{margin-bottom:27px}}.editor h2,.list-head h2{{margin:0;font-size:28px;line-height:1.15;letter-spacing:-.035em}}
      form{{display:grid;grid-template-columns:1fr 1fr;gap:17px}}label{{display:grid;gap:8px;font-size:14px;font-weight:700}}label:nth-of-type(3),label:nth-of-type(4){{grid-column:1/-1}}input,textarea{{width:100%;padding:14px;border:1px solid rgba(32,32,32,.18);border-radius:9px;outline:0;background:#fff;color:var(--ink);font:15px Manrope,Arial,sans-serif;transition:border-color .2s,box-shadow .2s}}input:focus,textarea:focus{{border-color:#3b8daf;box-shadow:0 0 0 4px rgba(59,141,175,.14)}}textarea{{min-height:112px;resize:vertical}}input[type=file]{{padding:11px;background:rgba(255,255,255,.82)}}.add-button{{grid-column:1/-1;justify-self:start;margin-top:4px;padding:15px 21px;border:0;border-radius:10px;background:var(--ink);color:#fff;font-weight:800;cursor:pointer;transition:transform .2s}}.add-button:hover{{transform:translateY(-2px)}}
      .list-head{{margin-bottom:27px}}#teacher-list{{display:grid;grid-template-columns:1fr;gap:24px}}.teacher-card{{min-width:0;display:grid;grid-template-columns:300px 1fr;overflow:hidden;border:1px solid #e3e5e1;border-radius:20px;background:#fff;box-shadow:0 8px 30px rgba(32,32,32,.05);transition:transform .25s,box-shadow .25s}}.teacher-card:hover{{transform:translateY(-4px);box-shadow:0 18px 42px rgba(32,32,32,.1)}}.teacher-card img{{width:100%;height:100%;min-height:330px;display:block;object-fit:cover;background:#eaf7fd}}.teacher-card-info{{display:flex;align-items:flex-start;justify-content:center;flex-direction:column;padding:34px 40px}}.teacher-card h2{{margin:0 0 12px;color:#202020;font-size:24px;line-height:1.2;letter-spacing:-.03em}}.teacher-card span{{display:inline-flex;align-items:center;padding:8px 12px;border-radius:50px;background:#bfe8f8;color:#202020;font-size:15px;font-weight:800}}.teacher-card p{{width:100%;margin:22px 0 0;padding-top:20px;border-top:1px solid #e3e5e1;color:#202020;font-size:18px;line-height:1.7}}.delete{{margin-top:24px;padding:10px 14px;border:1px solid rgba(181,78,66,.2);border-radius:8px;background:#fff;color:var(--danger);font-size:14px;font-weight:800;cursor:pointer}}.empty{{margin:0;padding:38px;border:1px dashed #bcc7c0;border-radius:14px;color:#202020;font-size:16px;text-align:center}}
      @media(max-width:700px){{.teacher-card{{grid-template-columns:1fr}}.teacher-card img{{height:310px;min-height:0}}.teacher-card-info{{padding:27px 23px}}}}
      @media(max-width:600px){{.admin-wrap{{width:min(100% - 32px,1060px)}}.admin-header{{height:78px}}.brand{{padding:13px 15px;font-size:17px}}.site-link{{font-size:12px}}main{{padding:48px 0 72px}}.editor{{margin:36px 0 60px;padding:25px 20px}}form{{grid-template-columns:1fr}}label:nth-of-type(3),label:nth-of-type(4),.add-button{{grid-column:auto}}}}
    </style></head>
    <body><div class="admin-topbar"><header class="admin-wrap admin-header"><a class="brand" href="/">СТИМУЛ</a><a class="site-link" href="/">Открыть сайт ↗</a></header></div>
    <main class="admin-wrap"><section><h1>Преподаватели</h1></section>
    <section class="editor"><div class="editor-head"><h2>Новый преподаватель</h2></div><form hx-post="/teachers" hx-encoding="multipart/form-data" hx-target="#teacher-list" hx-swap="innerHTML" hx-on::after-request="if(event.detail.successful) this.reset()">
      <label>Имя преподавателя<input name="name" autocomplete="name" required></label><label>Предмет<input name="subject" required></label><label>Краткая информация<textarea name="bio" required></textarea></label><label>Фотография<input name="photo" type="file" accept="image/jpeg,image/png,image/webp" required></label><button class="add-button" type="submit">Добавить преподавателя</button>
    </form></section><section><div class="list-head"><h2>Команда на сайте</h2></div><div id="teacher-list">{empty}{cards}</div></section></main></body></html>'''


def parse_multipart(content_type, body):
    message = BytesParser(policy=default).parsebytes(
        f"Content-Type: {content_type}\r\n\r\n".encode() + body
    )
    fields, uploaded_file = {}, None
    for part in message.iter_parts():
        name = part.get_param("name", header="content-disposition")
        filename = part.get_filename()
        if filename:
            uploaded_file = (filename, part.get_content_type(), part.get_payload(decode=True))
        elif name:
            raw_value = part.get_payload(decode=True)
            fields[name] = raw_value.decode("utf-8").strip()
    return fields, uploaded_file


class WebsiteHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/admin":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(admin_page().encode("utf-8"))
            return
        if path == "/diploma.png":
            logo = BASE_DIR / "diploma.png"
            if logo.is_file():
                self.send_response(200)
                self.send_header("Content-Type", "image/webp")
                self.end_headers()
                self.wfile.write(logo.read_bytes())
                return
            self.send_error(404)
            return
        if path.startswith("/uploads/"):
            file_path = UPLOADS_DIR / Path(path).name
            if file_path.is_file():
                self.send_response(200)
                self.send_header("Content-Type", mimetypes.guess_type(file_path.name)[0] or "application/octet-stream")
                self.end_headers()
                self.wfile.write(file_path.read_bytes())
                return
            self.send_error(404)
            return
        rendered_page = PAGE.replace("{{TEACHERS}}", render_public_teachers())
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(rendered_page.encode("utf-8"))


    def do_POST(self):
        path = urlparse(self.path).path
        if path == "/teachers":
            content_length = int(self.headers.get("Content-Length", 0))
            fields, uploaded_file = parse_multipart(
                self.headers.get("Content-Type", ""), self.rfile.read(content_length)
            )
            if not uploaded_file or not all(fields.get(key) for key in ("name", "subject", "bio")):
                self.send_error(400, "Заполните все поля и добавьте фотографию")
                return

            original_name, content_type, file_data = uploaded_file
            extension = Path(original_name).suffix.lower()
            allowed = {".jpg", ".jpeg", ".png", ".webp"}
            if extension not in allowed or content_type not in {"image/jpeg", "image/png", "image/webp"}:
                self.send_error(400, "Поддерживаются JPG, PNG и WebP")
                return

            UPLOADS_DIR.mkdir(exist_ok=True)
            filename = f"{uuid.uuid4().hex}{extension}"
            (UPLOADS_DIR / filename).write_bytes(file_data)
            teachers = load_teachers()
            teachers.append({
                "id": uuid.uuid4().hex,
                "name": fields["name"], "subject": fields["subject"],
                "bio": fields["bio"], "photo": f"/uploads/{filename}",
            })
            TEACHERS_FILE.write_text(json.dumps(teachers, ensure_ascii=False, indent=2), encoding="utf-8")
            response = "".join(render_admin_teacher(teacher) for teacher in teachers)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(response.encode("utf-8"))
            return

        self.send_error(404)

    def do_DELETE(self):
        match = re.fullmatch(r"/teachers/([a-f0-9]{32})", urlparse(self.path).path)
        if not match:
            self.send_error(404)
            return

        teacher_id = match.group(1)
        teachers = load_teachers()
        remaining = [teacher for teacher in teachers if teacher.get("id") != teacher_id]
        if len(remaining) == len(teachers):
            self.send_error(404)
            return

        TEACHERS_FILE.write_text(json.dumps(remaining, ensure_ascii=False, indent=2), encoding="utf-8")
        response = "".join(render_admin_teacher(teacher) for teacher in remaining)
        if not response:
            response = '<p class="empty">Пока не добавлено ни одного преподавателя.</p>'
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(response.encode("utf-8"))

    def log_message(self, format, *args):
        return


if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 8000), WebsiteHandler)
    print("Сайт доступен по адресу http://127.0.0.1:8000")
    server.serve_forever()
