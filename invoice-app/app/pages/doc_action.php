<?php
/** Document actions (POST): convert a proforma, cancel/restore an invoice, delete. */
defined('APP_DIR') || exit;

if (!is_post()) {
    redirect('home');
}
$id = (int) post('id');
$doc = doc_get($id);
if (!$doc) {
    not_found();
}

try {
    switch (post('action')) {
        case 'convert':
            $invId = doc_convert($id);
            $inv = doc_get($invId);
            flash('ok', 'فاکتور ' . $inv['number'] . ' صادر شد و مبلغ آن به بدهی مشتری اضافه شد.');
            redirect('doc', ['id' => $invId]);
            break;

        case 'cancel':
            if ($doc['type'] !== 'inv') {
                throw new UserError('فقط فاکتور باطل می‌شود.');
            }
            doc_set_status($id, 'cancelled');
            flash('ok', 'فاکتور ' . $doc['number'] . ' باطل شد و مبلغ آن از بدهی مشتری کم شد.');
            redirect('doc', ['id' => $id]);
            break;

        case 'restore':
            doc_set_status($id, 'active');
            flash('ok', 'فاکتور ' . $doc['number'] . ' بازگردانی شد و دوباره در بدهی مشتری حساب می‌شود.');
            redirect('doc', ['id' => $id]);
            break;

        case 'delete':
            if ($doc['type'] === 'inv' && $doc['status'] === 'active') {
                throw new UserError('فاکتور فعال حذف نمی‌شود؛ ابتدا آن را باطل کنید.');
            }
            doc_delete($id);
            flash('ok', DOC_NAMES[$doc['type']] . ' ' . $doc['number'] . ' حذف شد.');
            redirect('docs', ['type' => $doc['type']]);
            break;

        default:
            not_found();
    }
} catch (UserError $ex) {
    flash('err', $ex->getMessage());
    redirect('doc', ['id' => $id]);
}
