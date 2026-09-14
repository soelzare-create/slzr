// ============================================================
// DaranX site content — single source of truth.
// All copy is aligned with the Brand Skill: simple, professional,
// confident, direct. No exaggeration, no unnecessary jargon.
// Brand name is always written exactly as "DaranX".
// ============================================================

export const brand = {
  name: "DaranX",
  coreIdea: "همه چیز سر جای درستش.",
  promise: "فناوری قابل اعتماد برای رشد پایدار کسب‌وکارها.",
  philosophy: "طراحی مقدم بر اجراست.",
  belief: "اجرای دقیق یک طراحی اشتباه، همچنان یک نتیجه اشتباه است.",
  differentiator:
    "ما خدمات مختلف را کنار هم نمی‌گذاریم؛ آن‌ها را با هم طراحی می‌کنیم.",
  positioning: "شریک فناوری سازمان‌ها و کسب‌وکارها.",
};

// Navigation (section anchors)
export const nav = [
  { href: "#method", label: "روش کار" },
  { href: "#services", label: "حوزه‌ها" },
  { href: "#design", label: "طراحی" },
  { href: "#planogram", label: "PlanoGram" },
  { href: "#contact", label: "تماس" },
];

// شناخت ← طراحی ← اجرا ← پشتیبانی
export const method = [
  {
    key: "recognize",
    title: "شناخت",
    desc: "بررسی مسئله، نیاز، شرایط موجود و اهداف آینده سازمان. اول مسئله را می‌فهمیم، بعد راهکار پیشنهاد می‌کنیم.",
  },
  {
    key: "design",
    title: "طراحی",
    desc: "طراحی راهکار متناسب با نیاز واقعی و مشخص کردن جایگاه، ارتباط و نقش هر جزء در راهکار.",
  },
  {
    key: "execute",
    title: "اجرا",
    desc: "تبدیل طراحی به یک راهکار واقعی، با تجهیزات، فناوری و روش اجرایی مناسب.",
  },
  {
    key: "support",
    title: "پشتیبانی",
    desc: "رها نکردن نتیجه پس از اجرا؛ ادامه مسئولیت نگهداری، توسعه و عملکرد راهکار. نگاه پشتیبانی از همان مرحله طراحی آغاز می‌شود.",
  },
];

// Infrastructure · Security · Intelligence
export const services = [
  {
    key: "infrastructure",
    title: "Infrastructure",
    fa: "زیرساخت",
    tagline: "ساختن بستر درست.",
    desc: "زیرساختی که فناوری و عملیات سازمان روی آن قرار می‌گیرند.",
    items: [
      "Network",
      "Datacenter",
      "Server",
      "Storage",
      "Power & UPS",
      "Passive Infrastructure",
    ],
  },
  {
    key: "security",
    title: "Security",
    fa: "امنیت",
    tagline: "محافظت از آنچه ساخته‌ایم.",
    desc: "راهکارهایی برای محافظت از زیرساخت، محیط و دسترسی‌های سازمان.",
    items: ["Network Security", "CCTV", "Access & Monitoring", "کنترل تردد"],
  },
  {
    key: "intelligence",
    title: "Intelligence",
    fa: "هوشمندی",
    tagline: "هوشمند کردن آنچه ساخته و محافظت کرده‌ایم.",
    desc: "فناوری برای استفاده بهتر از داده، خودکارسازی و تصمیم‌گیری بهتر.",
    items: [
      "AI Solutions",
      "AI Assistants",
      "Data & Analytics",
      "Intelligent Automation",
      "Software Solutions",
      "Custom AI Models",
    ],
  },
];

// What sets DaranX apart (Brand Skill §6)
export const differentiators = [
  "اجزای مختلف بر اساس مسئله واقعی سازمان انتخاب می‌شوند.",
  "هر جزء جایگاه مشخصی در راهکار دارد.",
  "اجزا با یکدیگر سازگارند و برای یک هدف مشترک طراحی می‌شوند.",
  "نتیجه، یک راهکار منسجم است، نه مجموعه‌ای از تجهیزات.",
];

// Positioning: what DaranX is not / is (Brand Skill §9)
export const positioning = {
  not: [
    "صرفاً تجهیزات نمی‌فروشد.",
    "صرفاً پروژه اجرا نمی‌کند.",
    "صرفاً خدمات پشتیبانی ارائه نمی‌دهد.",
  ],
  is: "برای مسئله واقعی کسب‌وکار، راهکار طراحی می‌کند و مسئولیت نتیجه‌ی آن را ادامه می‌دهد.",
};

// PlanoGram venture (Brand Skill §16)
export const planogram = {
  name: "PlanoGram",
  tag: "Venture تحت DaranX",
  desc: "PlanoGram در حوزه چیدمان فروشگاهی، مدیریت قفسه‌ها و Planogram فعالیت می‌کند و بیشترین هم‌راستایی را با حوزه Intelligence دارد؛ چون از نرم‌افزار، داده و تحلیل برای تصمیم‌گیری بهتر درباره فضای فروش استفاده می‌کند.",
  capabilities: [
    "طراحی و مدیریت چیدمان فروشگاه",
    "مدیریت قفسه‌ها",
    "Planogram و استانداردسازی چیدمان",
    "استفاده از داده و نرم‌افزار برای تصمیم‌گیری درباره فضای فروش",
  ],
};
