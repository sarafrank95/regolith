from regolith.helpers.basehelper import SoutHelperBase
from regolith.dates import get_dates
from regolith.tools import fuzzy_retrieval, merge_collections_superior, all_docs_from_collection
from regolith.sorters import position_key
from datetime import date, timedelta
from regolith.helpers.makeappointmentshelper import _future_grant
from regolith.fsclient import _id_key


def subparser(subpi):
    subpi.add_argument("-d", "--date",
                       help="the date from which its current appointments will be listed, "
                            "defaults to today's date")
    return subpi

class CurrentAppointmentsHelper(SoutHelperBase):
    """Helper for managing appointments on grants and studying the burn of grants over time.
    """

    # btype must be the same as helper target in helper.py
    btype = 'currentappointments'
    needed_colls = ['people', "grants", "proposals"]

    def construct_global_ctx(self):
        """Constructs the global context"""
        super().construct_global_ctx()
        gtx = self.gtx
        rc = self.rc
        gtx["people"] = sorted(
            all_docs_from_collection(rc.client, "people"),
            key=position_key,
            reverse=True,
        )
        gtx["grants"] = sorted(
            all_docs_from_collection(rc.client, "grants"), key=_id_key
        )
        gtx["proposals"] = sorted(
            all_docs_from_collection(rc.client, "proposals"), key=_id_key
        )
        gtx["all_docs_from_collection"] = all_docs_from_collection
        gtx["float"] = float
        gtx["str"] = str
        gtx["zip"] = zip

    def sout(self):
        rc = self.rc
        if rc.date:
            ondate = date(*[int(num) for num in rc.date.split('-')])
        else:
            ondate = date.today()
        people = self.gtx['people']
        jg = self.gtx['grants']
        proposals = self.gtx["proposals"]
        grants = merge_collections_superior(proposals, jg, "proposal_id")
        _future_grant["begin_date"] = ondate
        _future_grant["end_date"] = ondate + timedelta(days=2190)
        _future_grant["budget"][0]["begin_date"] = ondate
        _future_grant["budget"][0]["end_date"] = ondate + timedelta(
            days=2190)
        grants.append(_future_grant)
        for person in people:
            p_appt = person.get('appointments', None)
            if p_appt:
                for _id, appt in p_appt.items():
                    grantid = appt.get('grant')
                    if not grantid:
                        print("No grant found in {} appt {}".format(person.get('_id'), k))
                    grant = fuzzy_retrieval(
                        grants,
                        ["name", "_id", "alias"],
                        grantid
                    )
                    if not grant:
                        print("No grant found for {}".format(grantid))
                    try:
                        accountnr = grant.get('account', grant['alias'])
                    except:
                        accountnr = ''
                    loading = appt.get('loading')
                    appt_dates = get_dates(appt)
                    bd = appt_dates.get('begin_date')
                    ed = appt_dates.get('end_date')
                    if ondate >= bd:
                        if ondate <= ed:
                            print(person.get('_id'), grantid, accountnr, loading,
                                  bd.strftime("%Y-%m-%d"),
                                  ed.strftime("%Y-%m-%d"))
