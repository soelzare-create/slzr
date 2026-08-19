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

// سمتِ فرد رابط در سازمان طرف‌حساب. Stored as the key; shown with the label.
export const CONTACT_POSITIONS = {
  ceo: "مدیرعامل",
  procurement: "خرید / بازرگانی",
  sales: "فروش",
  finance: "مالی / حسابداری",
  technical: "فنی / مهندسی",
  warehouse: "انباردار",
  staff: "کارشناس / کارمند",
  other: "سایر",
};

// Inventory (warehouse) vocabulary + write roles.
export const TRACKING_TYPE_FA = {
  serial: "سریال‌دار",
  quantity: "بدون سریال",
};

// Common units of measure (واحد شمارش) offered in the product form.
export const UNITS_OF_MEASURE = ["عدد", "متر", "کیلوگرم", "بسته", "رول", "لیتر"];

export const UNIT_STATUS_FA = {
  warehouse: "انبار",
  sold: "فروخته",
  installed: "نصب‌شده",
  broken: "خراب",
};

export const MOVEMENT_DIRECTION_FA = {
  in: "ورود",
  out: "خروج",
};

export const INVENTORY_WRITE_ROLES = ["manager", "warehouse"];

// Invoices (sales)
export const INVOICE_KIND_FA = {
  proforma: "پیش‌فاکتور",
  final: "فاکتور نهایی",
};

export const INVOICE_STATUS_FA = {
  unpaid: "پرداخت‌نشده",
  paid: "پرداخت‌شده",
  overdue: "معوق",
};

// Purchases (buying side)
export const PURCHASE_STATUS_FA = {
  unpaid: "پرداخت‌نشده",
  paid: "پرداخت‌شده",
  overdue: "معوق",
};

// Roles allowed to record purchases (mirrors backend RBAC).
export const PURCHASE_WRITE_ROLES = ["manager", "warehouse"];

// Accounting (financial documents / balances)
export const FINANCIAL_TYPE_FA = {
  income: "دخل",
  expense: "خرج",
};

// Roles allowed to read accounting (mirrors backend RBAC).
export const ACCOUNTING_ROLES = ["manager", "accountant"];

// Support / ticketing
export const TICKET_STATUS_FA = {
  open: "باز",
  investigating: "در حال بررسی",
  closed: "بسته",
};

// Roles allowed to create/edit tickets (mirrors backend RBAC).
export const SUPPORT_WRITE_ROLES = ["manager", "technical", "sales"];
