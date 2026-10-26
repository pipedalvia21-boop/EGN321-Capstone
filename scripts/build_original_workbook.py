"""Rebuild the ORIGINAL (inherited) spreadsheet, defects included.

This recreates GrowVest_Unit_Economics_v1.xlsx exactly as audited in
Assignment 3.2 so the capstone can show the starting point. The defects are
left in on purpose:

  R-01  Premium payment fee references Pro's price cell (Assumptions!C2).
  R-02  Stripe 2.9% + $0.30 typed as literals inside the Pro and Premium
        formulas, while an unused "Stripe %" input cell sits on Assumptions.
  R-03  (simulated) "Scenario" sheet: churn typed as 6 (meaning 6%) instead
        of 0.06. Excel accepts it and shows an LTV 100x too small.

Run:  python scripts/build_original_workbook.py
Then recalculate (cached values are needed by the verification tests):
      soffice --headless --convert-to xlsx --outdir original_workbook original_workbook/GrowVest_Unit_Economics_v1.xlsx
"""
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

OUT = Path(__file__).resolve().parent.parent / "original_workbook" / "GrowVest_Unit_Economics_v1.xlsx"
bold = Font(bold=True)
inp = PatternFill("solid", fgColor="FFF2CC")

wb = Workbook()
a = wb.active
a.title = "Assumptions"
a.append(["Input", "Free", "Pro", "Premium"])                 # row 1
a.append(["Price ($/mo)", 0, 29, 79])                          # row 2
a.append(["Hosting ($/user/mo)", 0.60, 3.20, 6.50])            # row 3
a.append(["Support ($/user/mo)", 0.10, 1.50, 4.00])            # row 4
a.append(["Monthly churn", 0.15, 0.06, 0.04])                  # row 5
a.append(["CAC ($)", 12, 85, 160])                             # row 6
a.append([])
a.append(["Stripe %", 0.029])                                  # row 8 (only Free uses it)
a.append(["Stripe fixed ($)", 0.30])                           # row 9
for row in a.iter_rows(min_row=2, max_row=9, min_col=2, max_col=4):
    for c in row:
        if c.value is not None:
            c.fill = inp
for c in a[1]:
    c.font = bold
a.column_dimensions["A"].width = 22

u = wb.create_sheet("Unit Economics")
u.append(["Output", "Free", "Pro", "Premium"])                 # row 1
u.append(["Payment fee",
          "=IF(Assumptions!B2=0,0,Assumptions!B2*Assumptions!B8+Assumptions!B9)",
          "=Assumptions!C2*0.029+0.3",                          # R-02 literal
          "=Assumptions!C2*0.029+0.3"])                         # R-01 + R-02
u.append(["Gross margin"] + [f"=Assumptions!{c}2-Assumptions!{c}3-Assumptions!{c}4-{c}2" for c in "BCD"])
u.append(["Margin %", '="n/a"', "=C3/Assumptions!C2", "=D3/Assumptions!D2"])
u.append(["LTV"] + [f"={c}3/Assumptions!{c}5" for c in "BCD"])
u.append(["CAC payback (mo)", '="n/a"', "=Assumptions!C6/C3", "=Assumptions!D6/D3"])
u.append(["LTV:CAC"] + [f"={c}5/Assumptions!{c}6" for c in "BCD"])
for c in u[1]:
    c.font = bold
u.column_dimensions["A"].width = 20

s = wb.create_sheet("Scenario")
s.append(["High-churn scenario for Pro (what-if)", "Value"])
s.append(["Price", "=Assumptions!C2"])
s.append(["Gross margin", "='Unit Economics'!C3"])
s.append(["Monthly churn (typed by analyst)", 6])               # R-03: meant 6%
s.append(["LTV", "=B3/B4"])
s[1][0].font = bold
s.column_dimensions["A"].width = 34

r = wb.create_sheet("Read Me")
for line in [
    "GrowVest unit economics model, v1 (inherited artifact).",
    "Yellow cells are inputs. All figures are per user per month.",
    "Prices are GrowVest's published tiers; costs, churn and CAC are simulated.",
    "KNOWN DEFECTS (Assignment 3.2 audit): R-01 Premium fee uses Pro price;",
    "R-02 Stripe fee hard-coded in formulas; R-03 churn accepted as whole percent.",
]:
    r.append([line])

OUT.parent.mkdir(exist_ok=True)
wb.save(OUT)
print("wrote", OUT)
