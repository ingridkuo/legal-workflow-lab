"""Build the shared synthetic intake and final register fixtures (no external data)."""
import json
from pathlib import Path
P = Path(__file__).parent
rows = []
names = [
 ('Harbor Office Interior Buildout','Cedar Electrical LLC','Lighting and distribution installation'),
 ('Riverside Clinic Upgrade','Cedar Vale Mechanical LLC','HVAC ductwork replacement'),
 ('Northgate Logistics Hub','Meridian Steelworks LLC','Structural steel fabrication and erection'),
 ('Eastbank Residential Phase II','Summit Facades LLC','External facade supply and installation'),
 ('Elm Street Retail Refresh','Pluto Interiors LLC','Joinery and interior finishes'),
 ('Civic Annex Retrofit','Pioneer Fire Systems LLC','Fire suppression retrofit'),
 ('Westfield School Renewal','Granite Civil LLC','Drainage and external works'),
 ('Brookside Library Extension','Maple Roofing LLC','Roofing and waterproofing'),
 ('Airport Service Building','Aster Controls LLC','Building controls integration'),
 ('Seaview Community Center','Oakline Landscaping LLC','Landscape and irrigation installation')
]
data = [
# id, amount, submitted, due, status, owner, exception, guarantee required/ref/expiry, insurance expiry, legal, senior, pm, finance, executive, sub sign, co sign
('001','50000.00','2026-11-09','2026-11-16','Legal Review','legal_001',False,False,'','','2027-03-31','Pending','Not required','Pending','Not required','Not required','',''),
('002','50000.01','2026-11-04','2026-11-10','Business Approval','pm_001',False,False,'','','2027-04-30','Approved','Not required','Pending','Pending','Not required','',''),
('003','250000.00','2026-11-01','2026-11-13','Ready for Signature','sub_signatory_003',False,True,'G-003','2026-11-25','2027-05-31','Approved','Not required','Approved','Approved','Not required','',''),
('004','250000.01','2026-10-28','2026-11-09','Business Approval','exec_001',False,True,'G-004','2027-02-28','2027-05-31','Approved','Not required','Approved','Approved','Pending','',''),
('005','12500.00','2026-11-06','2026-11-13','Legal Review','senior_legal_001',True,False,'','','2027-06-30','Approved','Pending','Pending','Not required','Not required','',''),
('006','80000.00','2026-11-02','2026-11-12','Hold','requester_006',False,True,'','','2027-01-31','Approved','Not required','Approved','Approved','Not required','',''),
('007','30000.00','2026-11-03','2026-11-09','Counterparty Signed','company_signatory_001',False,False,'','','2027-03-31','Approved','Not required','Approved','Not required','Not required','2026-11-06T12:00:00Z',''),
('008','40000.00','2026-10-29','2026-11-12','Executed','',False,True,'G-008','2026-12-05','2027-05-31','Approved','Not required','Approved','Not required','Not required','2026-11-09T12:00:00Z','2026-11-10T12:00:00Z'),
('009','100000.00','2026-11-03','2026-11-10','Rejected','',False,False,'','','2027-06-30','Rejected','Not required','Pending','Pending','Not required','',''),
('010','150000.00','2026-11-11','2026-11-18','Intake','requester_010',False,False,'','','2027-06-30','Pending','Not required','Pending','Pending','Not required','','')
]
for n, amount, submitted, due, status, owner, exceptional, gr, gref, gexp, iexp, legal, senior, pm, fin, exe, ss, cs in data:
    rows.append({
      'id': 'SC-'+n, 'project_name': names[int(n)-1][0],
      'subcontractor_name': names[int(n)-1][1],
      'scope': names[int(n)-1][2],
      'requestor_id': 'requester_'+n, 'subcontractor_signatory_id':'sub_signatory_'+n,
      'amount_usd': amount, 'currency':'USD', 'exceptional_terms':exceptional,
      'exception_notes':'Nonstandard limitation of liability; illustrative escalation only.' if exceptional else '',
      'submitted_at':submitted+'T09:00:00Z','needed_by_date':due,
      'planned_start_date':'2026-11-20','contract_expiry_date':'2027-06-30',
      'guarantee_required':gr,'guarantee_reference':gref,'guarantee_expiry_date':gexp,
      'insurance_required':True,'insurance_reference':'I-'+n,'insurance_expiry_date':iexp,
      'status':status,'current_owner':owner,
      'legal_approval':legal,'senior_legal_approval':senior,'project_manager_approval':pm,
      'finance_approval':fin,'executive_approval':exe,
      'subcontractor_signed_at':ss,'company_signed_at':cs,
      'execution_date':cs[:10] if cs else '',
      'hold_reason':'Missing required guarantee reference and expiry date' if status=='Hold' else ''
    })
(P/'sample_register.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
intake_keys = ['id','project_name','subcontractor_name','scope','requestor_id','subcontractor_signatory_id','amount_usd','currency','exceptional_terms','exception_notes','submitted_at','needed_by_date','planned_start_date','contract_expiry_date','guarantee_required','guarantee_reference','guarantee_expiry_date','insurance_required','insurance_reference','insurance_expiry_date']
(P/'example_intakes.json').write_text(json.dumps([{k:r[k] for k in intake_keys} for r in rows],indent=2)+'\n',encoding='utf-8')
