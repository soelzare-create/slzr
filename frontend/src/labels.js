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

// Roles allowed to create/edit CRM + activities (mirrors backend RBAC).
export const WRITE_ROLES = ["manager", "sales"];
