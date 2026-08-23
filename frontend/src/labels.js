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
// The most-used ones come first; "سایر" (custom) is handled by the form itself.
export const UNITS_OF_MEASURE = [
  "عدد",
  "دستگاه",
  "بسته",
  "متر",
  "حلقه",
  "رول",
  "کیلوگرم",
  "لیتر",
  "خدمت",
];

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
  partial: "قسمتی پرداخت‌شده",
  paid: "پرداخت‌شده",
  overdue: "معوق",
};

// Purchases (buying side)
export const PURCHASE_STATUS_FA = {
  unpaid: "پرداخت‌نشده",
  partial: "قسمتی پرداخت‌شده",
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

// Tasks / referrals (ارجاعات)
export const TASK_STATUS_FA = {
  assigned: "ارجاع‌شده",
  in_progress: "در حال انجام",
  done: "انجام‌شده",
};

// Payments / receipts (پرداخت / دریافت)
export const PAYMENT_DIRECTION_FA = {
  receipt: "دریافت",
  payment: "پرداخت",
};

export const PAYMENT_METHOD_FA = {
  cash: "نقد",
  card: "کارت",
  transfer: "حواله",
  cheque: "چک",
};

export const CASH_ACCOUNT_TYPE_FA = {
  cash: "صندوق",
  bank: "بانک",
};

export const CHEQUE_DIRECTION_FA = {
  received: "دریافتی",
  issued: "پرداختی",
};

export const CHEQUE_STATUS_FA = {
  registered: "در جریان",
  cleared: "وصول‌شده",
  bounced: "برگشتی",
};

// Common operating-expense categories (دستهٔ هزینه) offered in the voucher form.
export const EXPENSE_CATEGORIES = [
  "اجاره",
  "حقوق و دستمزد",
  "قبوض (آب/برق/گاز/تلفن)",
  "اینترنت",
  "ملزومات اداری",
  "حمل و نقل",
  "بازاریابی و تبلیغات",
  "مالیات و عوارض",
  "تعمیر و نگهداری",
  "سایر",
];
