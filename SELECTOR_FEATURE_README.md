# Local Body & Ward Selector Feature

## What Was Added

### 1. New Selector Page
**File:** `localbody_ward_selector.html`

A complete dropdown-based selector system that allows users to:
- Select a district from all 14 Kerala districts
- Choose a specific local body within that district
- Select individual wards using checkboxes
- Preview the selection before downloading
- Download a custom PDF with only selected wards

### 2. Updated Pages with Selector Button

All drill-down pages now have a **"📋 Select Specific Wards"** button in their preview modal:

- **ac.html** - Assembly Constituency drill-down
- **mandal.html** - Mandal drill-down  
- **localbody.html** - Local Body drill-down

### 3. Kerala Index Page
**File:** `kerala_index.html`

Added a prominent quick action button at the top:
- **"📋 Select & Download Local Body Wards"**

## How to Use

### From Kerala Index Page:
1. Open `http://localhost:8000/kerala_index.html`
2. Click the **"📋 Select & Download Local Body Wards"** button at the top
3. Follow the selector workflow

### From Drill-Down Pages (AC/Mandal/Local Body):
1. Navigate to any AC, Mandal, or Local Body view
2. Click the preview/download button to open the modal
3. Click **"📋 Select Specific Wards"** button
4. You'll be redirected to the selector page with context

## Selector Workflow

### Step 1: Select District
Choose from dropdown with all 14 districts:
- Thiruvananthapuram
- Kollam
- Pathanamthitta
- Alappuzha
- Kottayam
- Idukki
- Ernakulam
- Thrissur
- Palakkad
- Malappuram
- Kozhikode
- Wayanad
- Kannur
- Kasaragod

### Step 2: Select Local Body
Choose from all local bodies in the selected district
- Shows Corporation/Municipality/Panchayat type
- Displays total ward count

### Step 3: Select Wards
- Individual ward checkboxes with numbers and names
- **"Select All"** option at the top
- Live count of selected wards shown

### Step 4: Preview & Download
- Click **"👁️ Preview Selection"** to see selected wards
- Click **"📥 Download PDF"** to generate custom PDF
- PDF includes only selected local body and wards
- PDF filename: `LocalBodyName_NumberOfWards.pdf`

### Additional Options
- **"🔄 Reset"** - Clear all selections and start over
- Context indicator shows which page you came from

## Example Use Cases

### Example 1: Specific Wards from One Local Body
**Scenario:** Need only 5 wards from Kizhakkambalam Panchayat

1. Select **Ernakulam** district
2. Choose **Kizhakkambalam Panchayat**
3. Check Ward 1, 5, 10, 15, 20
4. Preview and download
5. Result: `Kizhakkambalam_Panchayat_5Wards.pdf`

### Example 2: All Wards from a Corporation
**Scenario:** Need all wards from Kochi Corporation

1. Select **Ernakulam** district
2. Choose **Kochi Corporation**
3. Click **"Select All"** (74 wards)
4. Download
5. Result: `Kochi_Corporation_74Wards.pdf`

### Example 3: Custom Selection
**Scenario:** Need specific wards for analysis

1. Select any district
2. Choose local body
3. Select only needed wards (e.g., wards 1-10)
4. Preview to verify
5. Download custom PDF

## Technical Details

### Files Modified
1. `localbody_ward_selector.html` - New selector page (created)
2. `ac.html` - Added selector button and function
3. `mandal.html` - Added selector button and function
4. `localbody.html` - Added selector button and function
5. `kerala_index.html` - Added quick action button and CSS

### Functions Added
Each drill-down page now has:
```javascript
function openCustomSelector() {
    const contextName = currentContext.name;
    window.location.href = `localbody_ward_selector.html?from=${encodeURIComponent(contextName)}`;
}
```

### Dependencies
- html2pdf.js (for PDF generation)
- Already included in existing pages

## Benefits

1. **Precise Control** - Select exactly which wards you need
2. **Saves Time** - No need to download entire datasets
3. **Smaller Files** - PDFs contain only selected data
4. **Better Organization** - Custom PDFs for specific requirements
5. **User Friendly** - Intuitive dropdown and checkbox interface

## Testing

Access the feature at:
- **Main Entry:** http://localhost:8000/kerala_index.html
- **Direct Access:** http://localhost:8000/localbody_ward_selector.html

Try these test scenarios:
1. Select a district and local body
2. Try "Select All" checkbox
3. Select individual wards
4. Preview before downloading
5. Download and verify PDF content

## Notes

- Context tracking shows which page you came from
- All 14 districts are supported
- Sample local bodies included for each district
- Can be easily extended with real data
- Responsive design works on all screen sizes
