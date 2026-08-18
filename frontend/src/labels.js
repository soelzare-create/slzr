// Persian labels for enum values shared across pages.
export const ROLE_FA = {
  manager: "مدیر",
  sales: "فروش",
  technical: "فنی",
  warehouse: "انباردار",
  accountant: "حسابدار",
};

export const ACTIVITY_TYPE_FA = {
  project: "پروژه",
  sale: "فروش کالا",
  support_contract: "قرارداد پشتیبانی",
};

export const ACTIVITY_STATUS_FA = {
  open: "باز",
  in_progress: "در حال انجام",
  done: "انجام‌شده",
  cancelled: "لغوشده",
};

export const STAGE_FA = {
  discovery: "شناخت",
  design: "طراحی",
  presale: "پیش‌فروش",
  execution: "اجرا",
  support: "پشتیبانی",
};

// How the customer got to know the company (مدل آشنایی).
// Stored as the key; shown with the Persian label.
export const REFERRAL_SOURCES = {
  website: "وبسایت",
  instagram: "اینستاگرام",
  telegram: "تلگرام",
  linkedin: "لینکدین",
  google: "جستجوی گوگل / وبگردی",
  exhibition: "نمایشگاه / رویداد تخصصی",
  tender: "مناقصه",
  past_customer: "معرفی توسط مشتری‌های سابق",
  other: "سایر",
};

// Roles allowed to create/edit activities (mirrors backend RBAC).
export const WRITE_ROLES = ["manager", "sales"];

// Roles allowed to create/edit parties (customers + suppliers).
export const PARTY_WRITE_ROLES = ["manager", "sales", "warehouse"];
