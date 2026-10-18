/* Parent app: plain JavaScript, no build step. Talks to /parent/* on the same server. */
(function () {
  "use strict";

  // ------------------------------------------------------------ text in both languages
  var T = {
    ur: {
      clinic: "کلینک",
      switchLang: "English",
      logout: "لاگ آؤٹ",
      loading: "لوڈ ہو رہا ہے...",
      back: "→ واپس",
      phoneTitle: "خوش آمدید",
      phoneIntro: "وہ موبائل نمبر لکھیں جو آپ نے کلینک میں دیا تھا۔ ہم اس پر 6 ہندسوں کا کوڈ بھیجیں گے۔",
      phoneLabel: "موبائل نمبر",
      sendCode: "کوڈ بھیجیں",
      codeTitle: "کوڈ لکھیں",
      codeIntro: "آپ کے نمبر پر 6 ہندسوں کا کوڈ بھیجا گیا ہے۔",
      codeLabel: "کوڈ",
      login: "لاگ ان",
      otherNumber: "دوسرا نمبر",
      noChildren: "آپ کے نمبر کے ساتھ کوئی بچہ درج نہیں۔ براہ مہربانی کلینک سے رابطہ کریں۔",
      hello: "السلام علیکم",
      emergencyLine: "ایمرجنسی؟",
      call1122: "1122 پر کال کریں",
      tileNow: "دورہ ابھی چل رہا ہے",
      tileNowSub: "ابھی کیا کریں",
      tileLog: "دورہ پڑا تھا",
      tileLogSub: "ڈاکٹر کو بتائیں",
      tileDoses: "آج کی دوائیاں",
      tileDosesSub: "دی یا نہیں دی",
      tileHelp: "سوال جواب",
      tileHelpSub: "ڈاکٹر کے جواب",
      tileSide: "کوئی اور مسئلہ",
      tileSideSub: "دوائی کا اثر",
      nowTitle: "دورہ ابھی چل رہا ہے",
      nowCall: "5 منٹ سے زیادہ ہو گئے؟ 1122 پر کال کریں",
      nowAfter: "دورہ ختم ہو جائے تو یہاں درج کریں",
      logTitle: "دورہ درج کریں",
      when: "کب ہوا؟",
      whenNow: "ابھی تھوڑی دیر پہلے",
      whenEarlier: "پہلے کسی وقت",
      whenPick: "تاریخ اور وقت",
      duration: "کتنی دیر چلا؟",
      dLt1: "1 منٹ سے کم",
      d1to2: "1 سے 2 منٹ",
      d2to5: "2 سے 5 منٹ",
      d5plus: "5 منٹ یا زیادہ",
      dUnknown: "پتہ نہیں",
      longHint: "اگر دورہ ابھی بھی چل رہا ہے تو فوراً 1122 پر کال کریں یا قریبی ایمرجنسی جائیں۔",
      unknownHint: "اندازہ لگانے کی کوشش کریں۔ اگر دورہ 5 منٹ یا اس سے زیادہ چلا ہو تو فوراً ایمرجنسی جائیں۔",
      kind: "کیسا تھا؟",
      kShaking: "جھٹکے",
      kStaring: "گم سم / گھورنا",
      kStiff: "جسم اکڑ گیا",
      kUnknown: "پتہ نہیں",
      fever: "بخار تھا؟",
      er: "ایمرجنسی گئے؟",
      yes: "ہاں",
      no: "نہیں",
      notes: "اور کچھ بتانا ہو (اختیاری)",
      save: "درج کریں",
      saving: "درج ہو رہا ہے...",
      chooseDuration: "براہ مہربانی بتائیں کہ دورہ کتنی دیر چلا۔",
      chooseTime: "براہ مہربانی تاریخ اور وقت لکھیں۔",
      savedTitle: "درج ہو گیا",
      savedBody: "ڈاکٹر صاحب اسے دیکھ لیں گے۔",
      alarmTitle: "فوراً ایمرجنسی جائیں",
      alarmOk: "ٹھیک ہے",
      home: "ہوم",
      dosesTitle: "آج کی دوائیاں",
      noMeds: "آج کے لیے کوئی دوائی درج نہیں۔",
      sTaken: "دی",
      sLate: "دیر سے دی",
      sMissed: "نہیں دی",
      sVomited: "الٹی ہو گئی",
      sNone: "ابھی درج نہیں",
      notYet: "ابھی وقت نہیں ہوا",
      helpTitle: "سوال جواب",
      helpIntro: "یہ جواب ڈاکٹر صاحب نے خود منظور کیے ہیں۔",
      noFaq: "ابھی کوئی جواب شامل نہیں کیا گیا۔",
      askTitle: "ڈاکٹر صاحب سے پوچھیں",
      askIntro: "اگر آپ کا سوال اوپر نہیں ہے تو یہاں لکھیں۔ جواب یہیں آئے گا۔ ایمرجنسی میں انتظار نہ کریں، 1122 پر کال کریں۔",
      askLabel: "آپ کا سوال",
      send: "بھیجیں",
      asked: "سوال بھیج دیا گیا۔",
      myQuestions: "آپ کے سوال",
      waiting: "جواب کا انتظار ہے",
      doctorSays: "ڈاکٹر:",
      sideTitle: "کوئی اور مسئلہ",
      sideIntro: "دوائی کے بعد جو تبدیلی دیکھیں وہ یہاں لکھیں، جیسے نیند، چڑچڑا پن، دانے۔",
      sideWhat: "کیا دیکھا؟",
      sideMed: "کس دوائی کے بعد؟ (اختیاری)",
      sideNoMed: "پتہ نہیں",
      sideDate: "کب سے؟",
      severity: "کتنا زیادہ؟",
      mild: "تھوڑا",
      moderate: "درمیانہ",
      severe: "بہت زیادہ",
      sideSaved: "درج ہو گیا۔ ڈاکٹر صاحب دیکھ لیں گے۔",
      sideUrgent: "اگر جلد پر دانے، منہ میں چھالے، آنکھیں پیلی، یا بار بار الٹی ہو تو آج ہی کلینک سے رابطہ کریں یا ایمرجنسی جائیں۔",
      error: "کچھ غلط ہو گیا۔ دوبارہ کوشش کریں۔",
      offline: "انٹرنیٹ یا سرور سے رابطہ نہیں ہو سکا۔",
      aiTitle: "اپنے الفاظ میں لکھیں",
      aiIntro: "جیسے: کل رات 3 منٹ دورہ پڑا، بخار بھی تھا۔ ہم فارم بھر دیں گے، آپ چیک کر کے محفوظ کریں۔",
      aiFill: "فارم بھریں",
      aiReading: "سمجھ رہے ہیں...",
      aiFilled: "ہم نے یہ سمجھا۔ نیچے چیک کریں اور ضرورت ہو تو بدلیں، پھر محفوظ کریں۔",
      aiMissing: "یہ نہیں سمجھ سکے، براہ مہربانی خود چنیں:",
      aiNotReport: "یہ دورے کی خبر نہیں لگتی۔ اگر سوال ہے تو 'سوال جواب' میں پوچھیں۔",
      aiRules: "(سادہ طریقے سے پڑھا گیا، AI استعمال نہیں ہوا)",
      fWhen: "کب",
      fDuration: "کتنی دیر",
      matchTitle: "شاید یہ آپ کا جواب ہے",
      matchNote: "یہ جواب ڈاکٹر صاحب کا منظور شدہ ہے۔",
      matchYes: "ہاں، جواب مل گیا",
      matchNo: "نہیں، ڈاکٹر سے پوچھیں",
      checking: "ڈھونڈ رہے ہیں...",
      tileSlip: "پرچی کی تصویر",
      tileSlipSub: "دوائیاں ڈاکٹر تک",
      slipTitle: "پرچی کی تصویر",
      slipIntro: "ڈاکٹر یا ہسپتال کی پرچی کی صاف تصویر لیں۔ ہم دوائیاں پڑھنے کی کوشش کریں گے، اور ڈاکٹر صاحب تصویر دیکھ کر منظور کریں گے۔",
      slipPick: "تصویر لیں یا چنیں",
      slipSending: "تصویر بھیج رہے ہیں...",
      slipRead: "ہم نے یہ دوائیاں پڑھیں:",
      slipUnclear: "صاف نہیں پڑھا گیا",
      slipConfirm: "ٹھیک ہے، ڈاکٹر کو بھیجیں",
      slipWrong: "کچھ غلط ہے، پھر بھی بھیجیں",
      slipSent: "بھیج دیا گیا۔ ڈاکٹر صاحب تصویر دیکھ کر منظور کریں گے۔",
      slipNone: "دوائیاں نہیں پڑھی جا سکیں۔ تصویر ڈاکٹر صاحب تک پہنچ گئی ہے۔",
      slipRecent: "پچھلی پرچیاں",
      stPending: "آپ کی تصدیق باقی",
      stConfirmed: "ڈاکٹر کے پاس",
      stVerified: "منظور",
      stRejected: "واپس",
      perDay: "دن میں",
      times: "بار",
    },
    en: {
      clinic: "Clinic",
      switchLang: "اردو",
      logout: "Log out",
      loading: "Loading...",
      back: "← Back",
      phoneTitle: "Welcome",
      phoneIntro: "Enter the mobile number you gave the clinic. We will send a 6-digit code to it.",
      phoneLabel: "Mobile number",
      sendCode: "Send code",
      codeTitle: "Enter the code",
      codeIntro: "A 6-digit code has been sent to your number.",
      codeLabel: "Code",
      login: "Log in",
      otherNumber: "Use another number",
      noChildren: "No child is linked to your number. Please contact the clinic.",
      hello: "Hello",
      emergencyLine: "Emergency?",
      call1122: "Call 1122",
      tileNow: "Seizure happening now",
      tileNowSub: "What to do right now",
      tileLog: "There was a seizure",
      tileLogSub: "Tell the doctor",
      tileDoses: "Today's medicines",
      tileDosesSub: "Given or not",
      tileHelp: "Questions",
      tileHelpSub: "The doctor's answers",
      tileSide: "Another problem",
      tileSideSub: "Medicine side effects",
      nowTitle: "Seizure happening now",
      nowCall: "Longer than 5 minutes? Call 1122",
      nowAfter: "When it is over, record it here",
      logTitle: "Record a seizure",
      when: "When did it happen?",
      whenNow: "Just now",
      whenEarlier: "Earlier",
      whenPick: "Date and time",
      duration: "How long did it last?",
      dLt1: "Under 1 minute",
      d1to2: "1 to 2 minutes",
      d2to5: "2 to 5 minutes",
      d5plus: "5 minutes or more",
      dUnknown: "Not sure",
      longHint: "If the seizure is still going on, call 1122 now or go to the nearest emergency room.",
      unknownHint: "Please try to estimate. If it lasted 5 minutes or longer, go to the emergency room now.",
      kind: "What did it look like?",
      kShaking: "Shaking",
      kStaring: "Staring / blank",
      kStiff: "Body went stiff",
      kUnknown: "Not sure",
      fever: "Was there a fever?",
      er: "Did you go to the emergency room?",
      yes: "Yes",
      no: "No",
      notes: "Anything else (optional)",
      save: "Save",
      saving: "Saving...",
      chooseDuration: "Please tell us how long the seizure lasted.",
      chooseTime: "Please enter the date and time.",
      savedTitle: "Saved",
      savedBody: "The doctor will see it.",
      alarmTitle: "Go to the emergency room now",
      alarmOk: "OK",
      home: "Home",
      dosesTitle: "Today's medicines",
      noMeds: "No medicines for today.",
      sTaken: "Given",
      sLate: "Given late",
      sMissed: "Not given",
      sVomited: "Vomited",
      sNone: "Not recorded",
      notYet: "Not time yet",
      helpTitle: "Questions",
      helpIntro: "These answers were approved by the doctor.",
      noFaq: "No answers have been added yet.",
      askTitle: "Ask the doctor",
      askIntro: "If your question is not above, write it here. The answer will appear here. In an emergency do not wait: call 1122.",
      askLabel: "Your question",
      send: "Send",
      asked: "Question sent.",
      myQuestions: "Your questions",
      waiting: "Waiting for an answer",
      doctorSays: "Doctor:",
      sideTitle: "Another problem",
      sideIntro: "Write any change you notice after the medicine, such as sleepiness, irritability or a rash.",
      sideWhat: "What did you notice?",
      sideMed: "After which medicine? (optional)",
      sideNoMed: "Not sure",
      sideDate: "Since when?",
      severity: "How bad?",
      mild: "Mild",
      moderate: "Moderate",
      severe: "Severe",
      sideSaved: "Saved. The doctor will see it.",
      sideUrgent: "If there is a skin rash, mouth sores, yellow eyes, or repeated vomiting, contact the clinic today or go to the emergency room.",
      error: "Something went wrong. Please try again.",
      offline: "Could not reach the server. Check your internet.",
      aiTitle: "Write it in your own words",
      aiIntro: "For example: last night a 3 minute seizure, with fever. We fill the form; you check it and save.",
      aiFill: "Fill the form",
      aiReading: "Reading...",
      aiFilled: "This is what we understood. Check below, change anything that is wrong, then save.",
      aiMissing: "We could not tell these, please choose:",
      aiNotReport: "This does not look like a seizure report. For a question, use Questions.",
      aiRules: "(read with simple rules, no AI)",
      fWhen: "when",
      fDuration: "how long",
      matchTitle: "Is this your answer?",
      matchNote: "This answer was approved by the doctor.",
      matchYes: "Yes, that answers it",
      matchNo: "No, ask the doctor",
      checking: "Looking...",
      tileSlip: "Prescription photo",
      tileSlipSub: "Medicines to the doctor",
      slipTitle: "Prescription photo",
      slipIntro: "Take a clear photo of the doctor's or hospital's slip. We will try to read the medicines, and the doctor will check the photo and approve them.",
      slipPick: "Take or choose a photo",
      slipSending: "Sending the photo...",
      slipRead: "We read these medicines:",
      slipUnclear: "not clearly read",
      slipConfirm: "Correct, send to the doctor",
      slipWrong: "Something is wrong, send anyway",
      slipSent: "Sent. The doctor will check the photo and approve.",
      slipNone: "The medicines could not be read. The photo has reached the doctor.",
      slipRecent: "Earlier slips",
      stPending: "Waiting for you",
      stConfirmed: "With the doctor",
      stVerified: "Approved",
      stRejected: "Returned",
      perDay: "a day",
      times: "times",
    },
  };

  var DURATIONS = [
    { key: "dLt1", seconds: 30 },
    { key: "d1to2", seconds: 90 },
    { key: "d2to5", seconds: 180 },
    { key: "d5plus", seconds: 300 },
    { key: "dUnknown", seconds: null },
  ];
  var KINDS = [
    { key: "kShaking", value: "shaking" },
    { key: "kStaring", value: "staring" },
    { key: "kStiff", value: "stiffening" },
    { key: "kUnknown", value: "unknown" },
  ];
  var STATUS_KEY = { taken: "sTaken", late: "sLate", missed: "sMissed", vomited: "sVomited" };

  // ------------------------------------------------------------ state
  var store = {
    get: function (k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } },
    set: function (k, v) { try { window.localStorage.setItem(k, v); } catch (e) { /* private mode */ } },
    del: function (k) { try { window.localStorage.removeItem(k); } catch (e) { /* private mode */ } },
  };
  var state = {
    lang: store.get("lang") === "en" ? "en" : "ur",
    token: store.get("token"),
    phone: "",
    guardian: null,
    children: [],
    childId: store.get("childId"),
  };
  var app = document.getElementById("app");

  function t(key) { return T[state.lang][key] || T.en[key] || key; }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function child() {
    for (var i = 0; i < state.children.length; i++) if (state.children[i].id === state.childId) return state.children[i];
    return state.children[0] || null;
  }
  function fmtTime(iso) {
    var d = new Date(iso);
    return d.toLocaleTimeString(state.lang === "ur" ? "ur-PK" : "en-GB", { hour: "2-digit", minute: "2-digit" });
  }
  function fmtDate(iso) {
    return new Date(iso).toLocaleString(state.lang === "ur" ? "ur-PK" : "en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" });
  }
  function todayLocal() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  function num(v) { var n = Number(v); return isFinite(n) ? String(Number(n.toFixed(2))) : String(v); }

  // ------------------------------------------------------------ server calls
  function api(path, options) {
    options = options || {};
    var headers = { "Content-Type": "application/json" };
    if (state.token) headers.Authorization = "Bearer " + state.token;
    return fetch(path, {
      method: options.method || "GET",
      headers: headers,
      body: options.body ? JSON.stringify(options.body) : undefined,
    }).then(
      function (res) {
        return res.json().catch(function () { return {}; }).then(function (data) {
          if (res.status === 401 && state.token) { signOut(); throw new Error("401"); }
          if (!res.ok) {
            var msg = typeof data.detail === "string" ? data.detail : t("error");
            var err = new Error(msg); err.status = res.status; throw err;
          }
          return data;
        });
      },
      function () { throw new Error(t("offline")); }
    );
  }

  // ------------------------------------------------------------ shell
  function applyLang() {
    document.documentElement.lang = state.lang;
    document.documentElement.dir = state.lang === "ur" ? "rtl" : "ltr";
    document.getElementById("lang-toggle").textContent = t("switchLang");
    var logout = document.getElementById("logout");
    logout.textContent = t("logout");
    logout.hidden = !state.token;
    var c = state.token ? child() : null;
    document.getElementById("topbar-title").textContent = c ? c.full_name : t("clinic");
    document.title = t("clinic");
  }
  function show(html) { applyLang(); app.innerHTML = html; window.scrollTo(0, 0); }
  function loading() { show('<p class="loading">' + esc(t("loading")) + "</p>"); }
  function errorBox(msg) { return '<p class="error" role="alert">' + esc(msg) + "</p>"; }
  function backButton() { return '<button type="button" class="back" data-go="home">' + esc(t("back")) + "</button>"; }
  function setBusy(form, busy, label) {
    var b = form.querySelector('button[type="submit"]');
    if (!b) return;
    if (busy) { b.dataset.label = b.textContent; b.textContent = label || t("saving"); b.disabled = true; }
    else { b.textContent = b.dataset.label || b.textContent; b.disabled = false; }
  }
  function showFormError(form, msg) {
    var box = form.querySelector(".form-error");
    if (box) box.innerHTML = errorBox(msg);
  }

  function signOut() {
    state.token = null; state.guardian = null; state.children = [];
    store.del("token");
    viewPhone();
  }

  // ------------------------------------------------------------ login
  function viewPhone(message) {
    show(
      '<section class="card">' +
        "<h1>" + esc(t("phoneTitle")) + "</h1>" +
        '<p class="muted">' + esc(t("phoneIntro")) + "</p>" +
        '<form id="phone-form" class="stack" novalidate>' +
          '<label for="phone">' + esc(t("phoneLabel")) + "</label>" +
          '<input id="phone" name="phone" type="tel" inputmode="tel" autocomplete="tel" placeholder="0300 1234567" value="' + esc(state.phone) + '" required>' +
          '<div class="form-error">' + (message ? errorBox(message) : "") + "</div>" +
          '<button type="submit" class="btn">' + esc(t("sendCode")) + "</button>" +
        "</form>" +
      "</section>"
    );
    document.getElementById("phone-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var form = e.target;
      state.phone = form.phone.value.trim();
      setBusy(form, true, t("loading"));
      api("/parent/auth/request-code", { method: "POST", body: { phone: state.phone } })
        .then(function () { viewCode(); })
        .catch(function (err) { setBusy(form, false); showFormError(form, err.message); });
    });
  }

  function viewCode(message) {
    show(
      '<section class="card">' +
        "<h1>" + esc(t("codeTitle")) + "</h1>" +
        '<p class="muted">' + esc(t("codeIntro")) + ' <span class="ltr">' + esc(state.phone) + "</span></p>" +
        '<form id="code-form" class="stack" novalidate>' +
          '<label for="code">' + esc(t("codeLabel")) + "</label>" +
          '<input id="code" name="code" class="code" type="text" inputmode="numeric" autocomplete="one-time-code" maxlength="6" pattern="[0-9]{6}" required>' +
          '<div class="form-error">' + (message ? errorBox(message) : "") + "</div>" +
          '<button type="submit" class="btn">' + esc(t("login")) + "</button>" +
          '<button type="button" class="btn btn-ghost" id="other-number">' + esc(t("otherNumber")) + "</button>" +
        "</form>" +
      "</section>"
    );
    document.getElementById("code").focus();
    document.getElementById("other-number").addEventListener("click", function () { viewPhone(); });
    document.getElementById("code-form").addEventListener("submit", function (e) {
      e.preventDefault();
      var form = e.target;
      var code = form.code.value.replace(/\D/g, "");
      setBusy(form, true, t("loading"));
      api("/parent/auth/verify", { method: "POST", body: { phone: state.phone, code: code } })
        .then(function (data) {
          state.token = data.token;
          store.set("token", data.token);
          return loadMe();
        })
        .catch(function (err) { setBusy(form, false); showFormError(form, err.message); });
    });
  }

  function loadMe() {
    loading();
    return api("/parent/me").then(function (data) {
      state.guardian = data.guardian;
      state.children = data.children || [];
      if (!child()) state.childId = null;
      if (!state.childId && state.children[0]) state.childId = state.children[0].id;
      if (state.childId) store.set("childId", state.childId);
      viewHome();
    }).catch(function (err) {
      if (err.message !== "401") show(errorBox(err.message) + '<button type="button" class="btn" id="retry">' + esc(t("login")) + "</button>");
      var r = document.getElementById("retry");
      if (r) r.addEventListener("click", loadMe);
    });
  }

  // ------------------------------------------------------------ home
  function viewHome() {
    var c = child();
    if (!c) { show('<section class="card"><p>' + esc(t("noChildren")) + "</p></section>"); return; }
    var switcher = "";
    if (state.children.length > 1) {
      switcher = '<div class="child-switch">' + state.children.map(function (k) {
        return '<button type="button" class="btn ' + (k.id === c.id ? "" : "btn-ghost") + '" data-child="' + esc(k.id) + '">' + esc(k.full_name) + "</button>";
      }).join("") + "</div>";
    }
    show(
      "<h1>" + esc(t("hello")) + (state.guardian ? ", " + esc(state.guardian.full_name) : "") + "</h1>" +
      switcher +
      '<div class="emergency-strip"><span>' + esc(t("emergencyLine")) + '</span><a href="tel:1122">' + esc(t("call1122")) + "</a></div>" +
      '<div class="tiles">' +
        tile("now", "tile-danger", t("tileNow"), t("tileNowSub")) +
        tile("log", "", t("tileLog"), t("tileLogSub")) +
        tile("doses", "", t("tileDoses"), t("tileDosesSub")) +
        tile("help", "", t("tileHelp"), t("tileHelpSub")) +
        tile("side", "", t("tileSide"), t("tileSideSub")) +
        tile("slip", "", t("tileSlip"), t("tileSlipSub")) +
      "</div>"
    );
    Array.prototype.forEach.call(app.querySelectorAll("[data-child]"), function (b) {
      b.addEventListener("click", function () { state.childId = b.dataset.child; store.set("childId", state.childId); viewHome(); });
    });
  }
  function tile(go, cls, title, sub) {
    return '<button type="button" class="tile ' + cls + '" data-go="' + go + '"><strong>' + esc(title) + "</strong><span>" + esc(sub) + "</span></button>";
  }

  // ------------------------------------------------------------ seizure happening now
  function viewNow() {
    loading();
    api("/parent/children/" + child().id + "/faq").then(function (faq) {
      var steps = faq.filter(function (f) { return f.topic === "first-aid" || f.topic === "emergency"; });
      var body = steps.map(function (f) {
        return '<section class="card"><h2>' + esc(state.lang === "ur" ? f.question_ur : f.question_en) + '</h2><p class="answer" style="padding:0">' +
          esc(state.lang === "ur" ? f.answer_ur : f.answer_en) + "</p></section>";
      }).join("");
      show(
        backButton() +
        '<div class="alarm"><h1>' + esc(t("nowTitle")) + '</h1><a class="btn" href="tel:1122">' + esc(t("nowCall")) + "</a></div>" +
        body +
        '<button type="button" class="btn btn-secondary" data-go="log">' + esc(t("nowAfter")) + "</button>"
      );
    }).catch(function (err) {
      if (err.message === "401") return;
      show(backButton() + '<div class="alarm"><h1>' + esc(t("nowTitle")) + '</h1><a class="btn" href="tel:1122">' + esc(t("nowCall")) + "</a></div>");
    });
  }

  // ------------------------------------------------------------ record a seizure
  function choice(name, value, label, extraClass, checked) {
    return '<label class="choice ' + (extraClass || "") + '"><input type="radio" name="' + name + '" value="' + esc(value) + '"' + (checked ? " checked" : "") + "><span>" + esc(label) + "</span></label>";
  }

  function setRadio(form, name, value) {
    var el = form.querySelector('input[name="' + name + '"][value="' + value + '"]');
    if (el) el.checked = true;
  }
  function bucketFor(seconds) {
    return seconds < 60 ? "dLt1" : seconds <= 120 ? "d1to2" : seconds < 300 ? "d2to5" : "d5plus";
  }
  function localInput(iso) {
    var d = new Date(iso);
    var p = function (n) { return String(n).padStart(2, "0"); };
    return d.getFullYear() + "-" + p(d.getMonth() + 1) + "-" + p(d.getDate()) + "T" + p(d.getHours()) + ":" + p(d.getMinutes());
  }

  function viewLog() {
    show(
      backButton() +
      '<section class="card">' +
        "<h1>" + esc(t("logTitle")) + "</h1>" +
        '<div class="ai-box stack"><label for="ai-text">' + esc(t("aiTitle")) + '</label>' +
          '<p class="muted small">' + esc(t("aiIntro")) + '</p>' +
          '<textarea id="ai-text" maxlength="2000"></textarea>' +
          '<button type="button" class="btn btn-secondary" id="ai-fill">' + esc(t("aiFill")) + '</button>' +
          '<div id="ai-result"></div></div>' +
        '<form id="seizure-form" class="stack" novalidate>' +
          "<fieldset><legend>" + esc(t("when")) + '</legend><div class="choices">' +
            choice("when", "now", t("whenNow"), "", true) + choice("when", "earlier", t("whenEarlier")) +
          '</div><div id="when-pick" hidden><label for="occurred">' + esc(t("whenPick")) + '</label><input id="occurred" type="datetime-local"></div></fieldset>' +
          "<fieldset><legend>" + esc(t("duration")) + '</legend><div class="choices">' +
            DURATIONS.map(function (d) { return choice("duration", d.key, t(d.key), d.key === "d5plus" ? "choice-danger" : ""); }).join("") +
          '</div><div id="duration-hint"></div></fieldset>' +
          "<fieldset><legend>" + esc(t("kind")) + '</legend><div class="choices">' +
            KINDS.map(function (k) { return choice("kind", k.value, t(k.key)); }).join("") +
          "</div></fieldset>" +
          "<fieldset><legend>" + esc(t("fever")) + '</legend><div class="choices">' +
            choice("fever", "yes", t("yes")) + choice("fever", "no", t("no")) +
          "</div></fieldset>" +
          "<fieldset><legend>" + esc(t("er")) + '</legend><div class="choices">' +
            choice("er", "yes", t("yes")) + choice("er", "no", t("no"), "", true) +
          "</div></fieldset>" +
          '<label for="notes">' + esc(t("notes")) + '</label><textarea id="notes" maxlength="2000"></textarea>' +
          '<div class="form-error"></div>' +
          '<button type="submit" class="btn">' + esc(t("save")) + "</button>" +
        "</form>" +
      "</section>"
    );
    var form = document.getElementById("seizure-form");
    var aiSeconds = null, aiBucket = null;
    document.getElementById("ai-fill").addEventListener("click", function () {
      var btn = this, text = document.getElementById("ai-text").value.trim(), box = document.getElementById("ai-result");
      if (text.length < 3) return;
      btn.disabled = true; btn.textContent = t("aiReading");
      api("/parent/children/" + child().id + "/ai/seizure-draft", { method: "POST", body: { text: text } }).then(function (r) {
        btn.disabled = false; btn.textContent = t("aiFill");
        if (!r.is_seizure_report) { box.innerHTML = '<p class="hint">' + esc(t("aiNotReport")) + "</p>"; return; }
        var d = r.draft;
        if (d.occurred_at) { setRadio(form, "when", "earlier"); document.getElementById("when-pick").hidden = false; document.getElementById("occurred").value = localInput(d.occurred_at); }
        aiSeconds = d.duration_seconds; aiBucket = null;
        if (d.duration_seconds !== null) { aiBucket = bucketFor(d.duration_seconds); setRadio(form, "duration", aiBucket); showDurationHint(aiBucket); }
        if (d.seizure_type) setRadio(form, "kind", d.seizure_type);
        if (d.fever_present !== null) setRadio(form, "fever", d.fever_present ? "yes" : "no");
        if (d.went_to_er !== null) setRadio(form, "er", d.went_to_er ? "yes" : "no");
        document.getElementById("notes").value = text;
        var missing = (r.missing || []).map(function (m) { return m === "occurred_at" ? t("fWhen") : t("fDuration"); });
        box.innerHTML = '<p class="success" role="status">' + esc(t("aiFilled")) + (r.source === "rules" ? " " + esc(t("aiRules")) : "") + "</p>" +
          (missing.length ? '<p class="hint">' + esc(t("aiMissing")) + " " + esc(missing.join("، ")) + "</p>" : "");
      }).catch(function (err) {
        btn.disabled = false; btn.textContent = t("aiFill");
        if (err.message !== "401") box.innerHTML = errorBox(err.message);
      });
    });
    function showDurationHint(value) {
      var hint = document.getElementById("duration-hint");
      hint.innerHTML = value === "d5plus" ? '<p class="hint" role="alert">' + esc(t("longHint")) + "</p>"
        : value === "dUnknown" ? '<p class="hint">' + esc(t("unknownHint")) + "</p>" : "";
    }
    form.addEventListener("change", function (e) {
      form.querySelector(".form-error").innerHTML = "";
      if (e.target.name === "when") document.getElementById("when-pick").hidden = e.target.value !== "earlier";
      if (e.target.name === "duration") showDurationHint(e.target.value);
    });
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var picked = form.querySelector('input[name="duration"]:checked');
      if (!picked) { showFormError(form, t("chooseDuration")); return; }
      var when = form.querySelector('input[name="when"]:checked').value;
      var occurred = new Date();
      if (when === "earlier") {
        var v = document.getElementById("occurred").value;
        if (!v) { showFormError(form, t("chooseTime")); return; }
        occurred = new Date(v);
      }
      var duration = DURATIONS.filter(function (d) { return d.key === picked.value; })[0];
      var kind = form.querySelector('input[name="kind"]:checked');
      var fever = form.querySelector('input[name="fever"]:checked');
      var er = form.querySelector('input[name="er"]:checked');
      var notes = document.getElementById("notes").value.trim();
      // Keep the exact seconds the parent wrote, unless they changed the choice.
      var seconds = picked.value === aiBucket && aiSeconds !== null ? aiSeconds : duration.seconds;
      var body = {
        occurred_at: occurred.toISOString(),
        duration_seconds: seconds,
        seizure_type: kind ? kind.value : null,
        fever_present: fever ? fever.value === "yes" : null,
        went_to_er: er ? er.value === "yes" : false,
        description: notes || null,
      };
      setBusy(form, true);
      api("/parent/children/" + child().id + "/seizures", { method: "POST", body: body })
        .then(function (res) { viewSeizureResult(res, seconds === null); })
        .catch(function (err) { if (err.message !== "401") { setBusy(form, false); showFormError(form, err.message); } });
    });
  }

  function viewSeizureResult(res, durationUnknown) {
    if (res.emergency_advice) {
      var msgs = (res.red_flags || []).map(function (f) {
        return "<p>" + esc(state.lang === "ur" ? f.message_ur : f.message_en) + "</p>";
      }).join("");
      show(
        '<div class="alarm" role="alert"><h1>' + esc(t("alarmTitle")) + "</h1>" + msgs +
        '<a class="btn" href="tel:1122">' + esc(t("call1122")) + "</a></div>" +
        '<button type="button" class="btn btn-ghost" data-go="home">' + esc(t("alarmOk")) + "</button>"
      );
      return;
    }
    show(
      '<section class="card"><h1>' + esc(t("savedTitle")) + '</h1><p class="success">' + esc(t("savedBody")) + "</p>" +
      (durationUnknown ? '<p class="hint">' + esc(t("unknownHint")) + "</p>" : "") +
      '<button type="button" class="btn" data-go="home">' + esc(t("home")) + "</button></section>"
    );
  }

  // ------------------------------------------------------------ today's doses
  function viewDoses() {
    loading();
    api("/parent/children/" + child().id + "/today").then(function (data) {
      var meds = data.medicines || [];
      var html = meds.length === 0 ? '<p class="muted">' + esc(t("noMeds")) + "</p>" : meds.map(function (m) {
        return '<div class="med"><h2>' + esc(m.drug_name) + ' <span class="muted ltr">' + esc(num(m.dose_amount) + " " + m.dose_unit) + "</span></h2>" +
          m.slots.map(function (s) {
            var statusKey = s.status ? STATUS_KEY[s.status] : "sNone";
            var buttons = s.due
              ? '<div class="slot-buttons">' +
                  doseButton(m.id, s.at, "taken", "sTaken", "") + doseButton(m.id, s.at, "missed", "sMissed", "btn-ghost") +
                  doseButton(m.id, s.at, "late", "sLate", "btn-ghost") + doseButton(m.id, s.at, "vomited", "sVomited", "btn-ghost") +
                "</div>"
              : '<p class="muted small">' + esc(t("notYet")) + "</p>";
            return '<div class="slot"><div class="slot-head"><span class="slot-time">' + esc(fmtTime(s.at)) + "</span>" +
              '<span class="status status-' + esc(s.status || "none") + '">' + esc(t(statusKey)) + "</span></div>" + buttons + "</div>";
          }).join("") + "</div>";
      }).join("");
      show(backButton() + '<section class="card"><h1>' + esc(t("dosesTitle")) + "</h1>" + html + '<div class="form-error"></div></section>');
      Array.prototype.forEach.call(app.querySelectorAll("[data-dose]"), function (b) {
        b.addEventListener("click", function () {
          b.disabled = true;
          api("/parent/children/" + child().id + "/doses", {
            method: "POST",
            body: { medication_id: b.dataset.med, scheduled_for: b.dataset.at, status: b.dataset.dose },
          }).then(viewDoses).catch(function (err) {
            b.disabled = false;
            var box = app.querySelector(".form-error"); if (box && err.message !== "401") box.innerHTML = errorBox(err.message);
          });
        });
      });
    }).catch(function (err) { if (err.message !== "401") show(backButton() + errorBox(err.message)); });
  }
  function doseButton(medId, at, status, key, cls) {
    return '<button type="button" class="btn ' + cls + '" data-dose="' + status + '" data-med="' + esc(medId) + '" data-at="' + esc(at) + '">' + esc(t(key)) + "</button>";
  }

  // ------------------------------------------------------------ questions
  function viewHelp(notice) {
    loading();
    var id = child().id;
    Promise.all([api("/parent/children/" + id + "/faq"), api("/parent/children/" + id + "/questions")]).then(function (r) {
      var faq = r[0], mine = r[1];
      var faqHtml = faq.length === 0 ? '<p class="muted">' + esc(t("noFaq")) + "</p>" : faq.map(function (f) {
        return '<details class="faq"><summary>' + esc(state.lang === "ur" ? f.question_ur : f.question_en) + "</summary>" +
          '<div class="answer">' + esc(state.lang === "ur" ? f.answer_ur : f.answer_en) + "</div></details>";
      }).join("");
      var mineHtml = mine.length === 0 ? "" : '<section class="card"><h2>' + esc(t("myQuestions")) + "</h2>" + mine.map(function (q) {
        return '<div class="question-item"><span class="muted small">' + esc(fmtDate(q.asked_at)) + "</span><p>" + esc(q.question) + "</p>" +
          (q.answer ? '<div class="doctor-answer"><strong>' + esc(t("doctorSays")) + "</strong> " + esc(q.answer) + "</div>"
                    : '<span class="status status-none">' + esc(t("waiting")) + "</span>") + "</div>";
      }).join("") + "</section>";
      show(
        backButton() +
        '<section class="card"><h1>' + esc(t("helpTitle")) + '</h1><p class="muted small">' + esc(t("helpIntro")) + '</p><div class="stack">' + faqHtml + "</div></section>" +
        '<section class="card"><h2>' + esc(t("askTitle")) + '</h2><p class="muted small">' + esc(t("askIntro")) + "</p>" +
          (notice ? '<p class="success" role="status">' + esc(notice) + "</p>" : "") +
          '<form id="ask-form" class="stack" novalidate><label for="question">' + esc(t("askLabel")) + "</label>" +
          '<textarea id="question" minlength="3" maxlength="1000" required></textarea><div class="form-error"></div>' +
          '<button type="submit" class="btn">' + esc(t("send")) + '</button></form><div id="match-box"></div></section>' +
        mineHtml
      );
      document.getElementById("ask-form").addEventListener("submit", function (e) {
        e.preventDefault();
        var form = e.target;
        var text = document.getElementById("question").value.trim();
        if (text.length < 3) { showFormError(form, t("askLabel")); return; }
        var send = function () {
          setBusy(form, true);
          api("/parent/children/" + id + "/questions", { method: "POST", body: { question: text } })
            .then(function () { viewHelp(t("asked")); })
            .catch(function (err) { if (err.message !== "401") { setBusy(form, false); showFormError(form, err.message); } });
        };
        setBusy(form, true, t("checking"));
        api("/parent/children/" + id + "/ai/match-question", { method: "POST", body: { question: text } }).then(function (r) {
          setBusy(form, false);
          if (!r.match) { send(); return; }
          var m = r.match;
          var box = document.getElementById("match-box");
          box.innerHTML = '<div class="match card"><h2>' + esc(t("matchTitle")) + "</h2>" +
            '<p class="label">' + esc(state.lang === "ur" ? m.question_ur : m.question_en) + "</p>" +
            '<p class="answer" style="padding:0">' + esc(state.lang === "ur" ? m.answer_ur : m.answer_en) + "</p>" +
            '<p class="muted small">' + esc(t("matchNote")) + "</p>" +
            '<div class="row"><button type="button" class="btn" id="match-yes">' + esc(t("matchYes")) + "</button>" +
            '<button type="button" class="btn btn-ghost" id="match-no">' + esc(t("matchNo")) + "</button></div></div>";
          box.scrollIntoView({ behavior: "smooth", block: "start" });
          document.getElementById("match-yes").addEventListener("click", function () { box.innerHTML = ""; document.getElementById("question").value = ""; });
          document.getElementById("match-no").addEventListener("click", function () { box.innerHTML = ""; send(); });
        }).catch(function (err) {
          if (err.message === "401") return;
          setBusy(form, false);
          send();  // matching is a convenience; the question still reaches the doctor
        });
      });
    }).catch(function (err) { if (err.message !== "401") show(backButton() + errorBox(err.message)); });
  }

  // ------------------------------------------------------------ side effects
  function viewSide() {
    loading();
    var id = child().id;
    api("/parent/children/" + id + "/today").then(function (data) {
      var meds = data.medicines || [];
      show(
        backButton() +
        '<section class="card"><h1>' + esc(t("sideTitle")) + '</h1><p class="muted">' + esc(t("sideIntro")) + "</p>" +
        '<p class="hint">' + esc(t("sideUrgent")) + "</p>" +
        '<form id="side-form" class="stack" novalidate>' +
          '<label for="what">' + esc(t("sideWhat")) + '</label><textarea id="what" maxlength="500" required></textarea>' +
          '<label for="med">' + esc(t("sideMed")) + '</label><select id="med"><option value="">' + esc(t("sideNoMed")) + "</option>" +
            meds.map(function (m) { return '<option value="' + esc(m.id) + '">' + esc(m.drug_name) + "</option>"; }).join("") + "</select>" +
          '<label for="since">' + esc(t("sideDate")) + '</label><input id="since" type="date" max="' + todayLocal() + '" value="' + todayLocal() + '">' +
          "<fieldset><legend>" + esc(t("severity")) + '</legend><div class="choices">' +
            choice("severity", "mild", t("mild")) + choice("severity", "moderate", t("moderate")) + choice("severity", "severe", t("severe")) +
          "</div></fieldset>" +
          '<div class="form-error"></div><button type="submit" class="btn">' + esc(t("save")) + "</button>" +
        "</form></section>"
      );
      document.getElementById("side-form").addEventListener("submit", function (e) {
        e.preventDefault();
        var form = e.target;
        var what = document.getElementById("what").value.trim();
        if (!what) { showFormError(form, t("sideWhat")); return; }
        var sev = form.querySelector('input[name="severity"]:checked');
        var body = {
          description: what,
          observed_on: document.getElementById("since").value || todayLocal(),
          medication_id: document.getElementById("med").value || null,
          severity: sev ? sev.value : null,
        };
        setBusy(form, true);
        api("/parent/children/" + id + "/side-effects", { method: "POST", body: body })
          .then(function () {
            show('<section class="card"><p class="success">' + esc(t("sideSaved")) + '</p><button type="button" class="btn" data-go="home">' + esc(t("home")) + "</button></section>");
          })
          .catch(function (err) { if (err.message !== "401") { setBusy(form, false); showFormError(form, err.message); } });
      });
    }).catch(function (err) { if (err.message !== "401") show(backButton() + errorBox(err.message)); });
  }

  // ------------------------------------------------------------ prescription photo
  var SLIP_STATUS = { pending: "stPending", parent_confirmed: "stConfirmed", doctor_verified: "stVerified", rejected: "stRejected" };

  function viewSlip(notice) {
    loading();
    var id = child().id;
    api("/parent/children/" + id + "/slips").then(function (slips) {
      var recent = slips.length === 0 ? "" : '<section class="card"><h2>' + esc(t("slipRecent")) + "</h2>" + slips.map(function (s) {
        var n = s.extracted_json && s.extracted_json.items ? s.extracted_json.items.length : 0;
        return '<div class="question-item"><span class="muted small">' + esc(fmtDate(s.uploaded_at)) + "</span>" +
          '<span class="row"><span class="status status-' + (s.status === "doctor_verified" ? "taken" : s.status === "rejected" ? "missed" : "none") + '">' +
          esc(t(SLIP_STATUS[s.status] || "stPending")) + "</span>" + (n ? '<span class="muted small">' + n + " ✓</span>" : "") + "</span>" +
          (s.reviewer_note ? '<div class="doctor-answer">' + esc(s.reviewer_note) + "</div>" : "") + "</div>";
      }).join("") + "</section>";
      show(
        backButton() +
        '<section class="card"><h1>' + esc(t("slipTitle")) + '</h1><p class="muted">' + esc(t("slipIntro")) + "</p>" +
        (notice ? '<p class="success" role="status">' + esc(notice) + "</p>" : "") +
        '<label class="btn" for="slip-file">' + esc(t("slipPick")) + "</label>" +
        '<input id="slip-file" type="file" accept="image/*" capture="environment" class="sr-only">' +
        '<div id="slip-result"></div></section>' + recent
      );
      document.getElementById("slip-file").addEventListener("change", function (e) {
        var file = e.target.files && e.target.files[0];
        if (!file) return;
        var out = document.getElementById("slip-result");
        out.innerHTML = '<p class="loading">' + esc(t("slipSending")) + "</p>";
        shrinkPhoto(file).then(function (b64) {
          return api("/parent/children/" + id + "/slips", { method: "POST", body: { mime_type: "image/jpeg", image_base64: b64 } });
        }).then(function (r) {
          var items = r.reading && r.reading.items ? r.reading.items : [];
          if (!items.length) { viewSlip(t("slipNone")); return; }
          out.innerHTML = '<div class="stack"><p class="label">' + esc(t("slipRead")) + '</p><ul class="slip-items">' + items.map(function (it) {
            var dose = [it.dose_amount !== null ? num(it.dose_amount) : "", it.dose_unit || ""].join(" ").trim();
            var times = it.times_per_day ? it.times_per_day + " " + t("times") + " " + t("perDay") : "";
            return "<li><strong>" + esc(it.drug_name) + "</strong> " + '<span class="ltr">' + esc(dose) + "</span>" +
              (times ? " · " + esc(times) : "") + (it.instructions ? '<br><span class="muted small">' + esc(it.instructions) + "</span>" : "") +
              (it.legible ? "" : ' <span class="status status-missed">' + esc(t("slipUnclear")) + "</span>") + "</li>";
          }).join("") + "</ul>" +
            '<button type="button" class="btn" id="slip-ok">' + esc(t("slipConfirm")) + "</button>" +
            '<button type="button" class="btn btn-ghost" id="slip-wrong">' + esc(t("slipWrong")) + "</button></div>";
          var confirm = function () {
            api("/parent/children/" + id + "/slips/" + r.id + "/confirm", { method: "POST" })
              .then(function () { viewSlip(t("slipSent")); })
              .catch(function (err) { if (err.message !== "401") out.innerHTML = errorBox(err.message); });
          };
          document.getElementById("slip-ok").addEventListener("click", confirm);
          document.getElementById("slip-wrong").addEventListener("click", confirm);
        }).catch(function (err) { if (err.message !== "401") out.innerHTML = errorBox(err.message); });
      });
    }).catch(function (err) { if (err.message !== "401") show(backButton() + errorBox(err.message)); });
  }

  // Phone photos are large; send at most 1600 px on the long side as JPEG.
  function shrinkPhoto(file) {
    return new Promise(function (resolve, reject) {
      var img = new Image();
      var url = URL.createObjectURL(file);
      img.onload = function () {
        var scale = Math.min(1, 1600 / Math.max(img.width, img.height));
        var c = document.createElement("canvas");
        c.width = Math.round(img.width * scale); c.height = Math.round(img.height * scale);
        c.getContext("2d").drawImage(img, 0, 0, c.width, c.height);
        URL.revokeObjectURL(url);
        resolve(c.toDataURL("image/jpeg", 0.85).split(",")[1]);
      };
      img.onerror = function () { URL.revokeObjectURL(url); reject(new Error(t("error"))); };
      img.src = url;
    });
  }

  // ------------------------------------------------------------ navigation
  var VIEWS = { home: viewHome, now: viewNow, log: viewLog, doses: viewDoses, help: viewHelp, side: viewSide, slip: viewSlip };
  app.addEventListener("click", function (e) {
    var target = e.target.closest("[data-go]");
    if (!target) return;
    var view = VIEWS[target.dataset.go];
    if (view) view();
  });
  document.getElementById("lang-toggle").addEventListener("click", function () {
    state.lang = state.lang === "ur" ? "en" : "ur";
    store.set("lang", state.lang);
    if (!state.token) viewPhone(); else if (state.children.length) viewHome(); else loadMe();
  });
  document.getElementById("logout").addEventListener("click", function () {
    var done = function () { signOut(); };
    api("/parent/auth/logout", { method: "POST" }).then(done, done);
  });

  if (state.token) loadMe(); else viewPhone();
})();
