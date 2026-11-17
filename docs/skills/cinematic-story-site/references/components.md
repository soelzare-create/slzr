# Reusable components (copy into the page)

## Demo / lead form (works with assets/engine/ui.js)
```html
<form class="form" id="demoForm" data-endpoint="" novalidate>
  <div class="errsum" id="errsum" role="alert" tabindex="-1" aria-labelledby="errtitle"><h3 id="errtitle">برای ارسال، این موارد را اصلاح کنید</h3><ul id="errlist"></ul></div>
  <div class="fields">
    <div class="field"><label for="f-name">نام و نام خانوادگی</label><input id="f-name" name="name" autocomplete="name" required aria-describedby="err-name"><p class="err" id="err-name"></p></div>
    <div class="field"><label for="f-company">نام شرکت</label><input id="f-company" name="company" autocomplete="organization" required aria-describedby="err-company"><p class="err" id="err-company"></p></div>
    <div class="field"><label for="f-phone">شمارهٔ تماس</label><input id="f-phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" dir="ltr" required aria-describedby="err-phone"><p class="err" id="err-phone"></p></div>
    <input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
    <button class="btn btn-brand" id="demoBtn" type="submit">ارسال</button>
    <p class="form-msg" id="formMsg" role="status" aria-live="polite"></p>
  </div>
  <div class="form-ok" role="status"><h3 id="okTitle">ثبت شد</h3><p>به‌زودی با شما تماس می‌گیریم.</p></div>
</form>
```
`data-endpoint` = URL that accepts JSON POST (form backend, Apps Script, webhook). Empty = shows "not configured". Validation rules live in ui.js `RULES` (translate messages for non-Persian sites).

## Plans / pricing (fits one screen)
```html
<section class="sec" id="plans"><div class="wrap">
  <h2>…</h2><p>هر پلن همهٔ امکانات پلن قبلی را دارد.</p>
  <div class="plans"><!-- 3–4 <article class="plan"> : small label, name (dir=ltr if Latin), one-line subtitle, "everything in X, plus:", 2–4 bullets, price at the bottom, last plan highlighted --></div>
</div></section>
```
List only what is new in each plan ("everything in Pro, plus: …"); repeating every feature makes cards too tall to fit one screen.

## FAQ
`<details><summary>Question</summary><p class="ans">Plain answer.</p></details>`; only answered questions go into FAQPage JSON-LD.

## Editor bar (keep outside #doc)
See assets/template/index.html (`#editbar` with edToggle/edSave/edDone/edDiscard/edStatus). Visible only on file:// or with `?edit`.
