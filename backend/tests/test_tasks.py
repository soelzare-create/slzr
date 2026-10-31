"""Tasks (کارها): one-sentence capture, routing, Bale bot, proforma link."""
from __future__ import annotations

from datetime import timedelta

import pytest
from django.utils import timezone

from apps.core.models import Notification, Party
from apps.sales.models import Proforma
from apps.tasks import bale, parsing, services
from apps.tasks.models import BaleLink, BaleMessage, Task

# Real commits, so after-commit notifications actually fire.
pytestmark = pytest.mark.django_db(transaction=True)

HOOK = "/api/bale/webhook/s3cret"


@pytest.fixture
def people(seeded, make_user):
    return {
        "soheil": make_user("09120000001", "سهیل زارع", "management"),
        "emad": make_user("09120000002", "عماد رضایی", "management"),
        "ali": make_user("09120000003", "علی محمدی", "technical_employee"),
        "sara": make_user("09120000004", "سارا احمدی", "sales_employee"),
    }


@pytest.fixture
def alpha(db):
    return Party.objects.create(name="شرکت آلفا", is_customer=True)


@pytest.fixture
def tg(settings, monkeypatch):
    """Bale enabled, delivered synchronously, API calls recorded."""
    settings.BALE_BOT_TOKEN = "123:abc"
    settings.BALE_SEND_ASYNC = False
    settings.BALE_WEBHOOK_SECRET = "s3cret"
    calls = []

    def fake(method, payload=None, timeout=10):
        calls.append((method, payload or {}))
        return {}

    monkeypatch.setattr(bale, "api_call", fake)
    return calls


def test_parse_understands_one_sentence(people, alpha):
    g = parsing.parse("آلفا سرورش از دیشب خاموشه @عماد")
    assert g.customer == alpha
    assert g.kind == Task.Kind.FAULT
    assert g.assignee == people["emad"]

    assert parsing.parse("نصب دوربین برای شرکت بتا").kind == Task.Kind.INSTALL
    assert parsing.parse("نصب دوربین برای شرکت بتا").customer_name == "شرکت بتا"
    assert parsing.parse("پروژه شبکه جدید").kind == Task.Kind.PROJECT
    assert parsing.parse("سوال درباره قرارداد").kind == Task.Kind.SUPPORT
    assert parsing.parse("بررسی کنید @مدیریت").mention_found is True
    # Arabic letters / ZWNJ are normalised
    assert parsing.parse("راه‌اندازی شبكه آلفا").kind == Task.Kind.INSTALL


def test_create_via_api_routes_and_notifies(people, alpha, api, tg):
    BaleLink.objects.create(user=people["emad"], chat_id=555)
    api.force_authenticate(people["ali"])
    with_cb = api.post("/api/tasks", {"text": "شرکت آلفا سرور خاموشه @عماد"}, format="json")
    assert with_cb.status_code == 201, with_cb.content
    task = Task.objects.get()
    assert task.number == "T-0001"
    assert (task.customer, task.assignee, task.kind) == (alpha, people["emad"], Task.Kind.FAULT)
    assert Notification.objects.filter(recipient=people["emad"], kind="TASK").exists()
    msg = BaleMessage.objects.get()
    assert msg.chat_id == 555 and msg.status == BaleMessage.Status.SENT
    assert "T-0001" in msg.text
    assert msg.reply_markup["inline_keyboard"][0][0]["callback_data"] == f"task:{task.pk}:start"


def test_unassigned_goes_to_management(people, api, tg):
    api.force_authenticate(people["ali"])
    api.post("/api/tasks", {"text": "مشتری جدید زنگ زد"}, format="json")
    task = Task.objects.get()
    assert task.assignee is None
    assert set(Notification.objects.values_list("recipient", flat=True)) == \
        {people["soheil"].pk, people["emad"].pk}


def test_explicit_overrides_win(people, alpha, api):
    api.force_authenticate(people["ali"])
    r = api.post("/api/tasks", {"text": "آلفا خرابی @عماد", "assignee": people["sara"].pk,
                                "kind": "PROJECT", "customer": None,
                                "customer_name": "مشتری تازه"}, format="json")
    t = Task.objects.get(pk=r.data["id"])
    assert t.assignee == people["sara"] and t.kind == "PROJECT"
    assert t.customer is None and t.customer_name == "مشتری تازه"


def test_visibility(people, api):
    services.create_task(text="کار علی", actor=people["ali"], assignee=people["emad"])
    services.create_task(text="کار سارا", actor=people["sara"], assignee=people["sara"])
    api.force_authenticate(people["ali"])
    assert [t["text"] for t in api.get("/api/tasks").data["results"]] == ["کار علی"]
    api.force_authenticate(people["soheil"])
    assert api.get("/api/tasks").data["count"] == 2
    other = Task.objects.get(text="کار سارا")
    api.force_authenticate(people["ali"])
    assert api.post(f"/api/tasks/{other.pk}/status", {"status": "DONE"}).status_code == 404


def test_status_and_reassign_flow(people, api, tg):
    task = services.create_task(text="نصب پرینتر", actor=people["sara"], assignee=people["ali"])
    api.force_authenticate(people["ali"])
    r = api.post(f"/api/tasks/{task.pk}/assign", {"assignee": people["emad"].pk}, format="json")
    assert r.status_code == 200 and r.data["assignee"] == people["emad"].pk
    api.force_authenticate(people["emad"])
    r = api.post(f"/api/tasks/{task.pk}/status", {"status": "DONE"}, format="json")
    assert r.data["status"] == "DONE"
    kinds = [e["kind"] for e in r.data["events"]]
    assert kinds == ["CREATED", "ASSIGNED", "STATUS"]
    # creator heard about it
    assert Notification.objects.filter(recipient=people["sara"], message__contains="انجام").exists()


def test_issue_proforma_from_task(people, api):
    task = services.create_task(text="پشتیبانی ماهانه شرکت گاما", actor=people["sara"],
                                assignee=people["sara"])
    assert task.customer is None and task.customer_name == "شرکت گاما"
    api.force_authenticate(people["sara"])
    r = api.post(f"/api/tasks/{task.pk}/proforma")
    assert r.status_code == 200, r.content
    pf = Proforma.objects.get(pk=r.data["proforma"])
    assert pf.customer.name == "شرکت گاما" and pf.lines.get().item.kind == "SERVICE"
    assert r.data["task"]["proforma_number"] == pf.number
    # idempotent
    assert api.post(f"/api/tasks/{task.pk}/proforma").data["proforma"] == pf.pk


def test_add_customer_one_click(people, api):
    task = services.create_task(text="خرابی فروشگاه دلتا", actor=people["ali"])
    api.force_authenticate(people["ali"])
    r = api.post(f"/api/tasks/{task.pk}/customer", {"create": True}, format="json")
    assert r.data["customer_display"] == "فروشگاه دلتا"
    assert Party.objects.filter(name="فروشگاه دلتا", is_customer=True).exists()


def test_reminder_after_24h(people, tg):
    task = services.create_task(text="کار قدیمی", actor=people["soheil"], assignee=people["ali"])
    Task.objects.filter(pk=task.pk).update(last_activity_at=timezone.now() - timedelta(hours=25))
    assert services.send_reminders() == 1
    assert services.send_reminders() == 0  # once per 24h
    assert Notification.objects.filter(recipient=people["ali"], message__contains="یادآوری").exists()


def test_bale_failure_never_breaks_task(people, settings, monkeypatch):
    settings.BALE_BOT_TOKEN = "123:abc"
    settings.BALE_SEND_ASYNC = False

    def boom(*a, **k):
        raise bale.BaleError("network down")

    monkeypatch.setattr(bale, "api_call", boom)
    BaleLink.objects.create(user=people["ali"], chat_id=1)
    task = services.create_task(text="x", actor=people["soheil"], assignee=people["ali"])
    assert Task.objects.filter(pk=task.pk).exists()
    msg = BaleMessage.objects.get()
    assert msg.status == BaleMessage.Status.PENDING and msg.attempts == 1


def test_link_account_by_shared_contact(people, api, tg):
    update = {"message": {"chat": {"id": 777, "type": "private"}, "from": {"id": 42},
                          "contact": {"user_id": 42, "phone_number": "+989120000003"}}}
    r = api.post(HOOK, update, format="json")
    assert r.status_code == 200
    assert BaleLink.objects.get(chat_id=777).user == people["ali"]
    # someone else's contact is refused
    bad = {"message": {"chat": {"id": 778, "type": "private"}, "from": {"id": 43},
                       "contact": {"user_id": 99, "phone_number": "09120000004"}}}
    api.post(HOOK, bad, format="json")
    assert not BaleLink.objects.filter(chat_id=778).exists()
    # wrong secret
    assert api.post("/api/bale/webhook/wrong", update, format="json").status_code == 404


def test_done_button_in_bale(people, api, tg):
    BaleLink.objects.create(user=people["ali"], chat_id=900)
    task = services.create_task(text="خرابی", actor=people["soheil"], assignee=people["ali"])
    update = {"callback_query": {"id": "cb1", "data": f"task:{task.pk}:done",
                                 "message": {"chat": {"id": 900}, "message_id": 5}}}
    api.post(HOOK, update, format="json")
    task.refresh_from_db()
    assert task.status == Task.Status.DONE
    assert any(m == "editMessageText" for m, _ in tg)


def test_done_button_refused_for_stranger(people, api, tg):
    BaleLink.objects.create(user=people["sara"], chat_id=901)
    task = services.create_task(text="خرابی", actor=people["soheil"], assignee=people["ali"])
    update = {"callback_query": {"id": "cb2", "data": f"task:{task.pk}:done",
                                 "message": {"chat": {"id": 901}, "message_id": 6}}}
    api.post(HOOK, update, format="json")
    task.refresh_from_db()
    assert task.status == Task.Status.OPEN


def test_link_account_with_one_time_code(people, api, tg):
    api.force_authenticate(people["sara"])
    st = api.get("/api/bale/status").data
    assert st["enabled"] and not st["linked"] and len(st["code"]) == 6
    # Persian digits are accepted, and "/start <code>" too
    fa_code = st["code"].translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))
    update = {"message": {"chat": {"id": 321, "type": "private"}, "from": {"id": 9},
                          "text": fa_code}}
    api.post(HOOK, update, format="json")
    assert BaleLink.objects.get(chat_id=321).user == people["sara"]
    assert api.get("/api/bale/status").data["linked"] is True
    # single use
    update["message"]["chat"]["id"] = 322
    api.post(HOOK, update, format="json")
    assert not BaleLink.objects.filter(chat_id=322).exists()
