"""History and persistence semantics, using the same model as HA writes."""
from copy import deepcopy
from datetime import date
import unittest
from custom_components.date_countdown.model import (
    initialize, validate_config, change_history, edit_item, values,
)

TODAY = date(2026, 11, 3)
NOW = "2026-11-03T12:00:00+08:00"


def lifetime():
    return initialize(validate_config({"name":"濾心","start_date":"2026-09-02",
        "duration":6,"unit":"months"}, TODAY), TODAY, NOW)


class HistoryTests(unittest.TestCase):
    def test_migration_idempotent(self):
        old={"name":"濾心","start_date":"2026-09-02","duration":6,"unit":"months"}
        item=initialize(old,TODAY,NOW)
        self.assertEqual(item,initialize(item,TODAY,"later"))
        self.assertNotIn("history",old)
        self.assertEqual(len(item["history"]),1)

    def test_add_backdated_keeps_latest(self):
        item=lifetime()
        new=change_history(item,"add",TODAY,NOW,day="2026-08-01",note="補登")
        self.assertEqual(new["start_date"],"2026-09-02")
        self.assertEqual(len(new["history"]),2)
        self.assertEqual(len(item["history"]),1)

    def test_delete_latest_reverts(self):
        item=change_history(lifetime(),"add",TODAY,NOW,day="2026-11-01")
        removed=change_history(item,"delete",TODAY,NOW,record_id=item["history"][-1]["id"])
        self.assertEqual(removed["start_date"],"2026-09-02")

    def test_cannot_delete_last(self):
        item=lifetime()
        with self.assertRaises(ValueError):
            change_history(item,"delete",TODAY,NOW,record_id=item["history"][0]["id"])

    def test_edit_history_recalculates(self):
        item=lifetime(); record_id=item["history"][0]["id"]
        edited=change_history(item,"edit",TODAY,NOW,day="2026-10-01",note="修正",record_id=record_id)
        self.assertEqual(edited["start_date"],"2026-10-01")
        self.assertEqual(values(edited,TODAY)[0],date(2027,4,1))
        self.assertEqual(edited["history"][0]["id"],record_id)

    def test_date_entity_edits_latest_without_losing_history(self):
        item=change_history(lifetime(),"add",TODAY,NOW,day="2026-11-01")
        edited=edit_item(item,{"start_date":"2026-08-01"},TODAY,NOW)
        self.assertEqual(edited["start_date"],"2026-09-02")
        self.assertEqual(len(edited["history"]),2)

    def test_fixed_due_change_has_audit(self):
        item=initialize(validate_config({"name":"保固","mode":"fixed","due_date":"2027-11-03"},TODAY),TODAY,NOW)
        edited=edit_item(item,{"due_date":"2028-11-03"},TODAY,NOW)
        self.assertEqual(edited["start_date"],item["start_date"])
        self.assertEqual(edited["history"][-1]["previous_due_date"],"2027-11-03")
        self.assertEqual(edited["history"][-1]["due_date"],"2028-11-03")
        with self.assertRaises(ValueError):
            change_history(edited,"add",TODAY,NOW,day=TODAY.isoformat())

    def test_due_today_and_expired_fixed(self):
        for day,remaining in [("2026-11-03",0),("2026-11-02",-1)]:
            item=initialize(validate_config({"name":"食品","mode":"fixed","due_date":day},TODAY),TODAY,NOW)
            self.assertEqual(values(item,TODAY),(date.fromisoformat(day),remaining,0))

    def test_reject_bad_input(self):
        base={"name":"濾心","start_date":"2026-09-02","duration":6,"unit":"months"}
        for patch in [{"duration":True},{"duration":1.5},{"reminder_days":-1},
                      {"name":" "},{"start_date":"20261103"},{"start_date":"2026-11-04"},{"unit":"seconds"},
                      {"duration":36500,"unit":"years"}]:
            with self.assertRaises((ValueError,OverflowError)):
                validate_config({**base,**patch},TODAY)

    def test_history_rejects_future_and_large_note(self):
        for day,note in [("2026-11-04",""),("2026-11-03","a"*2001)]:
            with self.assertRaises(ValueError):
                change_history(lifetime(),"add",TODAY,NOW,day=day,note=note)

    def test_metadata_update_preserves_history(self):
        item=lifetime()
        changed=edit_item(item,{"name":"新名稱","group":"淨水器","duration":12},TODAY,NOW)
        self.assertEqual(changed["history"],item["history"])
        self.assertEqual(changed["revision"],item["revision"]+1)
        self.assertNotEqual(values(item,TODAY),values(changed,TODAY))
