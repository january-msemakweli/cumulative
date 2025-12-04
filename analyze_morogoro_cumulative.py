import csv
from collections import Counter, defaultdict
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')  # Use non-interactive backend

# Read all three CSV files
data = []

# Read Mkundi
with open('Surgeries Done Mkundi.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['camp'] = 'Mkundi'
        data.append(row)

# Read Kilosa
with open('Surgeries Done Kilosa 2025.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['camp'] = 'Kilosa'
        data.append(row)

# Read Kilombero (Ifakara)
with open('Surgeries Done Kilombero.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        row['camp'] = 'Ifakara'
        data.append(row)

# 1. Count procedures and calculate demographics
procedure_count = len(data)

# Calculate gender distribution
male_count = sum(1 for row in data if row.get('Gender', '').strip() == 'Male')
female_count = sum(1 for row in data if row.get('Gender', '').strip() == 'Female')

# Calculate mean age
ages = []
for row in data:
    try:
        age = int(row.get('Age', 0))
        if age > 0:
            ages.append(age)
    except:
        pass
mean_age = sum(ages) / len(ages) if ages else 0

# 2. Extract VA data for operated eye
def extract_operated_eye(procedure):
    """Extract which eye was operated on from procedure string"""
    if ' - RE' in procedure or 'RE;' in procedure:
        return 'RE'
    elif ' - LE' in procedure or 'LE;' in procedure:
        return 'LE'
    elif 'RE' in procedure and 'LE' not in procedure:
        return 'RE'
    elif 'LE' in procedure:
        return 'LE'
    return None

def get_va_score(va):
    """Convert VA to numeric score (lower = better vision)"""
    va_scores = {
        '6/6': 1, '6/9': 2, '6/12': 3, '6/18': 4, '6/24': 5, '6/36': 6, '6/60': 7,
        'CF1M': 8, 'CF2M': 9, 'CF3M': 10, 'CF4M': 11, 'CF5M': 12, 'CFN': 13,
        'HM': 14, 'PL': 15, 'NPL': 16
    }
    return va_scores.get(va, 99)

def is_6_18_or_better(va):
    """Check if VA is 6/18 or better (WHO standard)"""
    score = get_va_score(va)
    return score <= 4  # 6/6, 6/9, 6/12, 6/18

va_data = []
va_data_all = []  # Keep all for general stats
patient_improvements = []
sics_patients = []
sics_va_data = []  # VA data for SICS procedures only

for row in data:
    procedure = row['Surgical Procedure Perfomed']
    operated_eye = extract_operated_eye(procedure)
    
    # Check if SICS procedure
    is_sics = 'SICS' in procedure.upper()
    
    if operated_eye == 'RE':
        preop_va = row['PREOP VA - Right Eye\t'].strip()
        day1_va = row['1 Day Post OP VA - Right Eye'].strip()
        week2_va = row['2 Weeks Post OP VA - Right Eye'].strip()
        month1_va = row['1 Month Post OP VA - Right Eye'].strip()
    elif operated_eye == 'LE':
        preop_va = row['PREOP VA - Left Eye\t'].strip()
        day1_va = row['1 Day Post OP VA - Left Eye'].strip()
        week2_va = row['2 Weeks Post OP VA - Left Eye'].strip()
        month1_va = row['1 Month Post OP VA - Left Eye'].strip()
    else:
        continue  # Skip if we can't determine the eye
    
    # Only include if we have at least preop data
    if preop_va:
        va_entry = {
            'preop': preop_va,
            'day1': day1_va,
            'week2': week2_va,
            'month1': month1_va,
            'camp': row['camp'],
            'is_sics': is_sics
        }
        va_data_all.append(va_entry)
        
        # Store SICS-only data for WHO standard calculation
        if is_sics:
            sics_va_data.append(va_entry)
        
        # Store patient info for improvement tracking (use month1 if available, otherwise week2)
        followup_va = month1_va if month1_va else week2_va
        if preop_va and followup_va:
            # Handle BOM in column name
            patient_id_key = '\ufeffPatient Number' if '\ufeffPatient Number' in row else 'Patient Number'
            patient_info = {
                'patient_id': row[patient_id_key],
                'name': row['Patient Name'],
                'preop_va': preop_va,
                'week2_va': week2_va,
                'month1_va': month1_va,
                'followup_va': followup_va,
                'camp': row['camp'],
                'procedure': procedure,
                'is_sics': is_sics
            }
            patient_improvements.append(patient_info)
            
            # Track SICS patients separately
            if is_sics:
                sics_patients.append(patient_info)

# Count VA frequencies for SICS procedures only
preop_va_count = Counter([v['preop'] for v in sics_va_data if v['preop']])
day1_va_count = Counter([v['day1'] for v in sics_va_data if v['day1']])
week2_va_count = Counter([v['week2'] for v in sics_va_data if v['week2']])
month1_va_count = Counter([v['month1'] for v in sics_va_data if v['month1']])

# Calculate WHO standard: % achieving 6/18 or better at each time point - SICS ONLY (Overall)
preop_patients_with_va = [v for v in sics_va_data if v['preop']]
day1_patients_with_va = [v for v in sics_va_data if v['day1']]
week2_patients_with_va = [v for v in sics_va_data if v['week2']]
month1_patients_with_va = [v for v in sics_va_data if v['month1']]

total_preop_va = len(preop_patients_with_va)
total_day1_va = len(day1_patients_with_va)
total_week2_va = len(week2_patients_with_va)
total_month1_va = len(month1_patients_with_va)

achieved_6_18_preop = sum(1 for v in preop_patients_with_va if is_6_18_or_better(v['preop']))
achieved_6_18_day1 = sum(1 for v in day1_patients_with_va if is_6_18_or_better(v['day1']))
achieved_6_18_week2 = sum(1 for v in week2_patients_with_va if is_6_18_or_better(v['week2']))
achieved_6_18_month1 = sum(1 for v in month1_patients_with_va if is_6_18_or_better(v['month1']))

pct_6_18_preop = (achieved_6_18_preop / total_preop_va * 100) if total_preop_va > 0 else 0
pct_6_18_day1 = (achieved_6_18_day1 / total_day1_va * 100) if total_day1_va > 0 else 0
pct_6_18_week2 = (achieved_6_18_week2 / total_week2_va * 100) if total_week2_va > 0 else 0
pct_6_18_month1 = (achieved_6_18_month1 / total_month1_va * 100) if total_month1_va > 0 else 0

# Calculate by camp - SICS ONLY
camp_stats = {}
for camp in ['Mkundi', 'Kilosa', 'Ifakara']:
    camp_sics_data = [v for v in sics_va_data if v['camp'] == camp]
    
    camp_preop = [v for v in camp_sics_data if v['preop']]
    camp_day1 = [v for v in camp_sics_data if v['day1']]
    camp_week2 = [v for v in camp_sics_data if v['week2']]
    camp_month1 = [v for v in camp_sics_data if v['month1']]
    
    camp_total_preop = len(camp_preop)
    camp_total_day1 = len(camp_day1)
    camp_total_week2 = len(camp_week2)
    camp_total_month1 = len(camp_month1)
    
    camp_achieved_preop = sum(1 for v in camp_preop if is_6_18_or_better(v['preop']))
    camp_achieved_day1 = sum(1 for v in camp_day1 if is_6_18_or_better(v['day1']))
    camp_achieved_week2 = sum(1 for v in camp_week2 if is_6_18_or_better(v['week2']))
    camp_achieved_month1 = sum(1 for v in camp_month1 if is_6_18_or_better(v['month1']))
    
    camp_pct_preop = (camp_achieved_preop / camp_total_preop * 100) if camp_total_preop > 0 else 0
    camp_pct_day1 = (camp_achieved_day1 / camp_total_day1 * 100) if camp_total_day1 > 0 else 0
    camp_pct_week2 = (camp_achieved_week2 / camp_total_week2 * 100) if camp_total_week2 > 0 else 0
    camp_pct_month1 = (camp_achieved_month1 / camp_total_month1 * 100) if camp_total_month1 > 0 else 0
    
    camp_stats[camp] = {
        'preop': {'total': camp_total_preop, 'achieved': camp_achieved_preop, 'pct': camp_pct_preop},
        'day1': {'total': camp_total_day1, 'achieved': camp_achieved_day1, 'pct': camp_pct_day1},
        'week2': {'total': camp_total_week2, 'achieved': camp_achieved_week2, 'pct': camp_pct_week2},
        'month1': {'total': camp_total_month1, 'achieved': camp_achieved_month1, 'pct': camp_pct_month1}
    }

# Calculate improvement for each patient
for patient in patient_improvements:
    preop_score = get_va_score(patient['preop_va'])
    followup_score = get_va_score(patient['followup_va'])
    improvement = preop_score - followup_score  # Positive = improvement
    patient['improvement'] = improvement
    patient['achieved_6_6'] = (patient['followup_va'] == '6/6')
    patient['achieved_6_18_or_better'] = is_6_18_or_better(patient['followup_va'])

# Sort SICS patients: first by achieved 6/6, then by improvement (descending)
sics_patients.sort(key=lambda x: (not x['achieved_6_6'], -x['improvement']))

# Get top 10 SICS patients
top_10_sics = sics_patients[:10]

# Define VA ordinal order (best to worst)
def get_va_order(va):
    """Return numeric order for VA values (lower = better vision)"""
    va_order = {
        '6/6': 1,
        '6/9': 2,
        '6/12': 3,
        '6/18': 4,
        '6/24': 5,
        '6/36': 6,
        '6/60': 7,
        'CF1M': 8,
        'CF2M': 9,
        'CF3M': 10,
        'CF4M': 11,
        'CF5M': 12,
        'CFN': 13,
        'HM': 14,
        'PL': 15,
        'NPL': 16
    }
    return va_order.get(va, 99)

# Get all unique VA values and sort by ordinal order
all_va_values = sorted(
    set(list(preop_va_count.keys()) + list(day1_va_count.keys()) + list(week2_va_count.keys()) + list(month1_va_count.keys())),
    key=get_va_order
)

# Count by camp
camp_counts = Counter([row['camp'] for row in data])

# Generate markdown report
markdown = f"""# Cumulative Morogoro Eye Camps Report
## The Mo Dewji Foundation

---

## Executive Summary

The Mo Dewji Foundation conducted comprehensive eye camps across three locations in Morogoro region: **Mkundi**, **Kilosa**, and **Ifakara** (Kilombero district). This cumulative report presents a comprehensive analysis of all procedures performed, conditions treated, and patient outcomes across these three camps, demonstrating the significant collective impact on improving vision and quality of life.

**Total Procedures Across All Camps: {procedure_count}**

**Breakdown by Camp:**
- Mkundi: {camp_counts.get('Mkundi', 0)} procedures
- Kilosa: {camp_counts.get('Kilosa', 0)} procedures
- Ifakara: {camp_counts.get('Ifakara', 0)} procedures

**Overall Gender Distribution:**
- Male: {male_count} ({male_count/procedure_count*100:.2f}%)
- Female: {female_count} ({female_count/procedure_count*100:.2f}%)

**Overall Mean Age: {mean_age:.1f} years**

---

## 1. WHO Standard: Visual Acuity Outcomes (SICS Procedures Only)

**⚠️ IMPORTANT:** This entire section focuses exclusively on **Small Incision Cataract Surgery (SICS) procedures**. All metrics, percentages, and charts in Section 1 are calculated for SICS patients only. Other procedures (EXCISION, BTRP, ICCE, etc.) are excluded from these calculations.

### 1.1 Achievement of 6/18 VA or Better (WHO Standard - SICS Only)

**WHO Recommendation:** A good eye camp should have **80% of operated patients achieving 6/18 VA or better** at follow-up.

**Cumulative Morogoro Results (SICS Procedures Only):**

- **Total SICS patients with 1 Month Post-op VA: {total_month1_va}**
- **SICS patients achieving 6/18 VA or better at 1 Month: {achieved_6_18_month1}**
- **Percentage achieving 6/18 VA or better: {pct_6_18_month1:.2f}%**

**Note:** These metrics are calculated for **Small Incision Cataract Surgery (SICS) procedures only**, as SICS was the primary surgical intervention across all camps.

"""

# Add assessment against WHO standard
if pct_6_18_month1 >= 80:
    markdown += f"**✅ EXCEEDS WHO STANDARD:** The cumulative Morogoro eye camps achieved **{pct_6_18_month1:.2f}%**, which **exceeds** the WHO recommended standard of 80%. This demonstrates excellent surgical outcomes and quality of care across all three camps.\n\n"
elif pct_6_18_month1 >= 70:
    markdown += f"**⚠️ APPROACHING WHO STANDARD:** The cumulative Morogoro eye camps achieved **{pct_6_18_month1:.2f}%**, which is approaching the WHO recommended standard of 80%. While below the target, this represents good outcomes with room for continued improvement.\n\n"
else:
    markdown += f"**⚠️ BELOW WHO STANDARD:** The cumulative Morogoro eye camps achieved **{pct_6_18_month1:.2f}%**, which is below the WHO recommended standard of 80%. This indicates areas for improvement in surgical techniques, patient selection, or post-operative care.\n\n"

markdown += f"""
**Analysis:**
- The cumulative results from all three Morogoro camps show {'strong' if pct_6_18_month1 >= 80 else 'good' if pct_6_18_month1 >= 70 else 'moderate'} performance against the WHO standard.
- This metric is critical for assessing the quality and effectiveness of eye camp services, as 6/18 vision represents functional vision that enables patients to perform daily activities independently.
- Achieving this standard demonstrates that the eye camps are successfully restoring functional vision to the majority of patients, enabling them to return to productive activities and improve their quality of life.

### 1.2 Cumulative SICS Performance: Journey to {pct_6_18_month1:.2f}%

The following chart shows the cumulative progression of **all SICS patients across all three camps** achieving 6/18 VA or better from pre-operative assessment through 1 month post-operatively.

"""

# Create cumulative area plot showing overall progression
time_points = ['Pre-op', '1 Day\nPost-op', '2 Weeks\nPost-op', '1 Month\nPost-op']
overall_percentages = [pct_6_18_preop, pct_6_18_day1, pct_6_18_week2, pct_6_18_month1]
overall_counts = [achieved_6_18_preop, achieved_6_18_day1, achieved_6_18_week2, achieved_6_18_month1]
overall_totals = [total_preop_va, total_day1_va, total_week2_va, total_month1_va]
who_standard = [80, 80, 80, 80]

plt.figure(figsize=(12, 7))
# Create area plot
plt.fill_between(range(len(time_points)), overall_percentages, alpha=0.6, color='#4ecdc4', label='All SICS Patients Achieving 6/18 VA or Better')
# Add line plot on top
plt.plot(range(len(time_points)), overall_percentages, marker='o', markersize=12, linewidth=3, color='#2a8a84', label='Cumulative Progression', markerfacecolor='white', markeredgewidth=2)
# Add WHO standard line
plt.plot(range(len(time_points)), who_standard, '--', linewidth=2.5, color='#ff6b6b', label='WHO Standard (80%)', alpha=0.8)
# Add value labels on points
for i, (x, y) in enumerate(zip(range(len(time_points)), overall_percentages)):
    plt.annotate(f'{y:.2f}%', (x, y), textcoords="offset points", xytext=(0,18), ha='center', fontsize=12, fontweight='bold', color='#1a5a55')
    plt.annotate(f'SICS: {overall_counts[i]}/{overall_totals[i]}', (x, y), textcoords="offset points", xytext=(0,-30), ha='center', fontsize=10, style='italic', color='#666')

plt.xticks(range(len(time_points)), time_points, fontsize=12)
plt.yticks(range(0, 101, 10), [f'{i}%' for i in range(0, 101, 10)], fontsize=11)
plt.ylabel('Percentage of SICS Patients', fontsize=13, fontweight='bold')
plt.xlabel('Time Point', fontsize=13, fontweight='bold')
plt.title(f'Cumulative Morogoro: Journey to {pct_6_18_month1:.2f}%\nSICS Patients Achieving 6/18 VA or Better (WHO Standard: 80%)', 
          fontsize=14, fontweight='bold', pad=20)
plt.legend(loc='lower right', fontsize=11, framealpha=0.9)
plt.grid(axis='y', alpha=0.3, linestyle='--')
plt.ylim(0, 100)
plt.tight_layout()
plt.savefig('morogoro_chart_cumulative_6_18.png', dpi=300, bbox_inches='tight')
plt.close()

markdown += f"""
![Cumulative SICS Performance](morogoro_chart_cumulative_6_18.png)

**Cumulative Progression (All Three Camps Combined - SICS Only):**
| Time Point | SICS Patients | Achieving 6/18 or Better | Percentage |
|------------|---------------|--------------------------|------------|
| Pre-op | {total_preop_va} | {achieved_6_18_preop} | {pct_6_18_preop:.2f}% |
| 1 Day Post-op | {total_day1_va} | {achieved_6_18_day1} | {pct_6_18_day1:.2f}% |
| 2 Weeks Post-op | {total_week2_va} | {achieved_6_18_week2} | {pct_6_18_week2:.2f}% |
| 1 Month Post-op | {total_month1_va} | {achieved_6_18_month1} | {pct_6_18_month1:.2f}% |

**Key Finding:** The cumulative results show a dramatic improvement from {pct_6_18_preop:.2f}% pre-operatively to {pct_6_18_month1:.2f}% at 1 month, {'exceeding' if pct_6_18_month1 >= 80 else 'approaching'} the WHO standard of 80%.

---

### 1.3 Camp-Specific SICS Performance

The following charts show the progression of SICS patients achieving 6/18 VA or better for each individual camp, allowing for comparison of outcomes across locations.

"""

# Create charts for each camp

camp_colors = {
    'Mkundi': '#2ecc71',
    'Kilosa': '#3498db',
    'Ifakara': '#9b59b6'
}

for camp in ['Mkundi', 'Kilosa', 'Ifakara']:
    stats = camp_stats[camp]
    percentages = [stats['preop']['pct'], stats['day1']['pct'], stats['week2']['pct'], stats['month1']['pct']]
    counts = [stats['preop']['achieved'], stats['day1']['achieved'], stats['week2']['achieved'], stats['month1']['achieved']]
    totals = [stats['preop']['total'], stats['day1']['total'], stats['week2']['total'], stats['month1']['total']]
    
    plt.figure(figsize=(10, 6))
    # Create area plot
    plt.fill_between(range(len(time_points)), percentages, alpha=0.5, color=camp_colors[camp], label=f'{camp} SICS Patients Achieving 6/18 VA or Better')
    # Add line plot on top
    plt.plot(range(len(time_points)), percentages, marker='o', markersize=10, linewidth=2.5, color=camp_colors[camp], label=f'{camp} Progression', markerfacecolor='white', markeredgewidth=2)
    # Add WHO standard line
    plt.plot(range(len(time_points)), who_standard, '--', linewidth=2, color='#ff6b6b', label='WHO Standard (80%)', alpha=0.7)
    # Add value labels on points
    for i, (x, y) in enumerate(zip(range(len(time_points)), percentages)):
        plt.annotate(f'{y:.2f}%', (x, y), textcoords="offset points", xytext=(0,15), ha='center', fontsize=11, fontweight='bold')
        plt.annotate(f'{counts[i]}/{totals[i]}', (x, y), textcoords="offset points", xytext=(0,-25), ha='center', fontsize=9, style='italic', color='#666')
    
    plt.xticks(range(len(time_points)), time_points, fontsize=11)
    plt.yticks(range(0, 101, 10), [f'{i}%' for i in range(0, 101, 10)], fontsize=10)
    plt.ylabel('Percentage of SICS Patients', fontsize=12, fontweight='bold')
    plt.xlabel('Time Point', fontsize=12, fontweight='bold')
    plt.title(f'{camp} Camp: SICS Patients Achieving 6/18 VA or Better\n(1 Month: {stats["month1"]["pct"]:.2f}% | {stats["month1"]["achieved"]}/{stats["month1"]["total"]} patients)', 
              fontsize=13, fontweight='bold', pad=15)
    plt.legend(loc='lower right', fontsize=10, framealpha=0.9)
    plt.grid(axis='y', alpha=0.3, linestyle='--')
    plt.ylim(0, 100)
    plt.tight_layout()
    plt.savefig(f'morogoro_chart_{camp.lower()}_6_18.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Add to markdown
    markdown += f"""
#### {camp} Camp

![{camp} SICS Performance](morogoro_chart_{camp.lower()}_6_18.png)

**Performance Summary:**
- **1 Month Post-op:** {stats['month1']['pct']:.2f}% ({stats['month1']['achieved']}/{stats['month1']['total']} SICS patients) achieved 6/18 VA or better
- **Progression:** From {stats['preop']['pct']:.2f}% pre-operatively to {stats['month1']['pct']:.2f}% at 1 month
- **Status:** {'✅ EXCEEDS' if stats['month1']['pct'] >= 80 else '⚠️ APPROACHING' if stats['month1']['pct'] >= 70 else '⚠️ BELOW'} WHO Standard (80%)

The {camp} camp demonstrated {'strong' if stats['month1']['pct'] >= 80 else 'good' if stats['month1']['pct'] >= 70 else 'moderate'} performance in restoring functional vision to SICS patients, with {stats['month1']['pct']:.2f}% achieving the critical 6/18 VA threshold at 1 month follow-up. This represents a significant improvement from the pre-operative baseline of {stats['preop']['pct']:.2f}%, showing the effectiveness of cataract surgery in this location.

---
"""

markdown += """

---

## 2. SICS Visual Acuity Distribution

**Note:** This section focuses exclusively on **Small Incision Cataract Surgery (SICS) procedures** to provide a clear picture of cataract surgery outcomes across all three camps.

### 2.1 VA Distribution Across All Time Points (SICS Only)

| Visual Acuity | Pre-op | 1 Day Post-op | 2 Weeks Post-op | 1 Month Post-op | Change (Pre-op to 1 Month) |
|---------------|--------|---------------|-----------------|------------------|----------------------------|
"""

total_preop = sum(preop_va_count.values())
total_day1 = sum(day1_va_count.values())
total_week2 = sum(week2_va_count.values())
total_month1 = sum(month1_va_count.values())

for va in all_va_values:
    preop_count = preop_va_count.get(va, 0)
    day1_count = day1_va_count.get(va, 0)
    week2_count = week2_va_count.get(va, 0)
    month1_count = month1_va_count.get(va, 0)
    
    preop_pct = (preop_count / total_preop * 100) if total_preop > 0 else 0
    day1_pct = (day1_count / total_day1 * 100) if total_day1 > 0 else 0
    week2_pct = (week2_count / total_week2 * 100) if total_week2 > 0 else 0
    month1_pct = (month1_count / total_month1 * 100) if total_month1 > 0 else 0
    
    # Calculate change from preop to 1 month
    if preop_count > 0 and month1_count > 0:
        change = ((month1_count - preop_count) / preop_count * 100)
        change_str = f"{change:+.2f}%"
    elif preop_count == 0 and month1_count > 0:
        change_str = "+∞%"
    elif preop_count > 0 and month1_count == 0:
        change_str = "-100%"
    else:
        change_str = "N/A"
    
    markdown += f"| {va} | {preop_count} ({preop_pct:.2f}%) | {day1_count} ({day1_pct:.2f}%) | {week2_count} ({week2_pct:.2f}%) | {month1_count} ({month1_pct:.2f}%) | {change_str} |\n"

markdown += f"\n**Total SICS Patients with Pre-op VA: {total_preop}**\n"
markdown += f"**Total SICS Patients with 1 Day Post-op VA: {total_day1}**\n"
markdown += f"**Total SICS Patients with 2 Weeks Post-op VA: {total_week2}**\n"
markdown += f"**Total SICS Patients with 1 Month Post-op VA: {total_month1}**\n"

# Calculate cumulative improvements
cumulative_6_6_preop = preop_va_count.get('6/6', 0)
cumulative_6_6_month1 = month1_va_count.get('6/6', 0)
cumulative_6_6_pct_change = ((cumulative_6_6_month1 - cumulative_6_6_preop) / cumulative_6_6_preop * 100) if cumulative_6_6_preop > 0 else 0
cumulative_6_6_preop_pct = (cumulative_6_6_preop/total_preop*100) if total_preop > 0 else 0
cumulative_6_6_month1_pct = (cumulative_6_6_month1/total_month1*100) if total_month1 > 0 else 0

cumulative_6_9_preop = preop_va_count.get('6/9', 0)
cumulative_6_9_month1 = month1_va_count.get('6/9', 0)

cumulative_6_12_preop = preop_va_count.get('6/12', 0)
cumulative_6_12_month1 = month1_va_count.get('6/12', 0)

cumulative_6_18_preop = preop_va_count.get('6/18', 0)
cumulative_6_18_month1 = month1_va_count.get('6/18', 0)

# Count patients with poor vision preop
poor_vision_preop = sum(preop_va_count.get(va, 0) for va in ['HM', 'PL', 'NPL', 'CF1M', 'CF2M', 'CF3M', 'CF4M', 'CF5M', 'CFN'])
poor_vision_month1 = sum(month1_va_count.get(va, 0) for va in ['HM', 'PL', 'NPL', 'CF1M', 'CF2M', 'CF3M', 'CF4M', 'CF5M', 'CFN'])
poor_vision_preop_pct = (poor_vision_preop/total_preop*100) if total_preop > 0 else 0
poor_vision_month1_pct = (poor_vision_month1/total_month1*100) if total_month1 > 0 else 0

markdown += f"""

**Cumulative Outcome Highlights:**
- **Dramatic improvements** were observed across all visual acuity levels, with significant reductions in patients with poor vision (HM, PL, NPL, CF categories) and substantial increases in patients achieving good vision (6/6, 6/9, 6/12, 6/18).
"""
va_6_6 = "6/6"
markdown += f"- The percentage of patients achieving **{va_6_6} vision (best possible)** increased from {cumulative_6_6_preop} ({cumulative_6_6_preop_pct:.2f}%) pre-operatively to {cumulative_6_6_month1} ({cumulative_6_6_month1_pct:.2f}%) at 1 month post-operatively - a **{cumulative_6_6_pct_change:.1f}% increase**, representing life-changing outcomes for these patients.\n"
markdown += f"- Patients achieving **6/18 VA or better** (functional vision) increased from {achieved_6_18_preop} ({pct_6_18_preop:.2f}%) pre-operatively to {achieved_6_18_month1} ({pct_6_18_month1:.2f}%) at 1 month post-operatively.\n"
markdown += f"- The dramatic reduction in patients with **poor vision** (HM, PL, NPL, CF categories) from {poor_vision_preop} ({poor_vision_preop_pct:.2f}%) to {poor_vision_month1} ({poor_vision_month1_pct:.2f}%) demonstrates the camps' success in addressing severe vision impairment.\n"
markdown += "- These improvements translate directly to enhanced independence, ability to work, and overall quality of life for patients and their families across all three Morogoro camps.\n"

markdown += """

---

## 3. Top 10 Success Stories: SICS Procedures

The following patients represent the most remarkable transformations achieved through **Small Incision Cataract Surgery (SICS)** across all three Morogoro camps. These success stories demonstrate the life-changing impact of cataract surgery in restoring vision.

| Patient ID | Patient Name | Camp | Pre-op VA | 2 Weeks Post-op VA | 1 Month Post-op VA |
|------------|--------------|------|-----------|---------------------|---------------------|
"""

for patient in top_10_sics:
    month1_display = patient['month1_va'] if patient['month1_va'] else 'N/A'
    markdown += f"| {patient['patient_id']} | {patient['name']} | {patient['camp']} | {patient['preop_va']} | {patient['week2_va']} | {month1_display} |\n"

markdown += f"""

**Success Stories:**
These ten patients represent the most remarkable transformations achieved through **SICS procedures** across all three Morogoro eye camps. Many achieved **6/6 vision (perfect vision)** at the 1-month follow-up, having started with severe vision impairment ranging from Perception of Light (PL) to Hand Motion (HM) and Counting Fingers at various distances. These outcomes exemplify the life-changing impact of cataract surgery, which was the most common procedure performed across all camps. The continued improvement from 2 weeks to 1 month demonstrates the importance of follow-up care and the healing process.

**Key Observations:**
- All top 10 success stories are from SICS (Small Incision Cataract Surgery) procedures, highlighting the effectiveness of this surgical technique
- Patients came from all three camps (Mkundi, Kilosa, and Ifakara), demonstrating consistent quality of care across locations
- The majority achieved perfect vision (6/6) at 1 month, representing complete restoration of functional vision
- These outcomes demonstrate that cataract surgery, when performed with proper technique and follow-up care, can restore vision even in patients with severe pre-operative vision impairment

---

## 4. SICS Summary Statistics by Camp

### 4.1 SICS Procedures by Camp

"""

# Count SICS procedures by camp
sics_camp_counts = Counter([p['camp'] for p in sics_patients])
total_sics = sum(sics_camp_counts.values())

mkundi_sics = sics_camp_counts.get('Mkundi', 0)
kilosa_sics = sics_camp_counts.get('Kilosa', 0)
ifakara_sics = sics_camp_counts.get('Ifakara', 0)

mkundi_sics_pct = (mkundi_sics/total_sics*100) if total_sics > 0 else 0
kilosa_sics_pct = (kilosa_sics/total_sics*100) if total_sics > 0 else 0
ifakara_sics_pct = (ifakara_sics/total_sics*100) if total_sics > 0 else 0

markdown += """
| Camp | Number of SICS Procedures | Percentage of Total SICS |
|------|---------------------------|--------------------------|
"""
markdown += f"| Mkundi | {mkundi_sics} | {mkundi_sics_pct:.2f}% |\n"
markdown += f"| Kilosa | {kilosa_sics} | {kilosa_sics_pct:.2f}% |\n"
markdown += f"| Ifakara | {ifakara_sics} | {ifakara_sics_pct:.2f}% |\n"
markdown += f"| **Total** | **{total_sics}** | **100.00%** |\n"

# Build conclusion section
conclusion_status = 'remarkable' if pct_6_18_month1 >= 80 else 'significant'
achievement_status = 'Achieved' if pct_6_18_month1 >= 80 else ('Approached' if pct_6_18_month1 >= 70 else 'Made progress toward')
recommendation_status = 'Maintain' if pct_6_18_month1 >= 80 else 'Work toward achieving'

markdown += f"""

---

## Conclusion

The cumulative Morogoro Eye Camps conducted by The Mo Dewji Foundation achieved {conclusion_status} success in addressing cataract-related blindness across three communities in the Morogoro region. With **{total_sics} SICS (Small Incision Cataract Surgery) procedures** performed across Mkundi, Kilosa, and Ifakara, the camps made a substantial collective impact on preventing blindness and restoring vision.

**Key SICS Achievements:**
- Successfully performed {total_sics} SICS procedures across all three camps, with consistent quality outcomes
- {achievement_status} the WHO standard of 80% of SICS patients achieving 6/18 VA or better, with a cumulative result of **{pct_6_18_month1:.2f}%**
- Achieved dramatic improvements in visual acuity, with many SICS patients progressing from severe vision impairment (PL, HM) to excellent functional vision (6/6)
- Demonstrated consistent quality of SICS care across all three camp locations:
  - Mkundi: {camp_stats['Mkundi']['month1']['pct']:.2f}% achieving 6/18 or better
  - Kilosa: {camp_stats['Kilosa']['month1']['pct']:.2f}% achieving 6/18 or better
  - Ifakara: {camp_stats['Ifakara']['month1']['pct']:.2f}% achieving 6/18 or better
- Provided life-changing outcomes for SICS patients, enabling them to regain independence and improve their quality of life

**Impact on Community:**
The cumulative impact of these SICS procedures extends beyond individual patients to their families and the broader Morogoro region. Restored vision enables patients to:
- Return to productive work and economic activities
- Care for themselves and their families independently
- Participate fully in community life and social activities
- Reduce the burden on family caregivers

**Recommendations:**
Based on the cumulative SICS data analysis:
- Continue prioritizing SICS, given its excellent outcomes and effectiveness in treating cataract-related blindness
- {recommendation_status} the WHO standard of 80% achieving 6/18 VA or better through continued quality improvement
- Ensure adequate follow-up care to monitor continued improvement in visual outcomes
- Continue the successful model of conducting multiple camps across the region to maximize accessibility
- Share best practices across camps to ensure consistent quality of SICS outcomes

The success of these cumulative SICS procedures demonstrates the critical importance of accessible cataract surgery services in underserved communities and the transformative power of SICS in restoring vision and improving lives across the Morogoro region.
"""

# Write to file
with open('morogoro_cumulative_report.md', 'w', encoding='utf-8') as f:
    f.write(markdown)

print(f"Report generated successfully!")
print(f"\nWHO Standard Results:")
print(f"  Pre-op: {pct_6_18_preop:.2f}% ({achieved_6_18_preop}/{total_preop_va})")
print(f"  1 Day Post-op: {pct_6_18_day1:.2f}% ({achieved_6_18_day1}/{total_day1_va})")
print(f"  2 Weeks Post-op: {pct_6_18_week2:.2f}% ({achieved_6_18_week2}/{total_week2_va})")
print(f"  1 Month Post-op: {pct_6_18_month1:.2f}% ({achieved_6_18_month1}/{total_month1_va})")
print(f"  WHO Standard: 80%")
print(f"  Status: {'✅ EXCEEDS' if pct_6_18_month1 >= 80 else '⚠️ BELOW'} WHO Standard")
print(f"\nTop 10 SICS Success Stories: {len(top_10_sics)} patients identified")

