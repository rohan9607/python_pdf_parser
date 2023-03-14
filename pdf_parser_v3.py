import re
import json
from PyPDF2 import PdfReader

two_numbers_pattern = "([+-]?[0-9]+([.][0-9]*)?)"
right_dash_number_pattern = "([-+]?[0-9]*\.[0-9]+)\s[-]"
left_dash_number_pattern = "[-]\s([-+]?[0-9]*\.[0-9]+)"
file = PdfReader("KSSL Signed FS March 2021.pdf")


# Get Page number
def get_page_no(file):
    pageNo = 0
    for page in file.pages:
        success_ratio = 0
        text = page.extract_text()
        if bool(re.search("Balance", text, re.IGNORECASE)):
            success_ratio += 1
        if bool(re.search("Non\s?-\s?current", text, re.IGNORECASE)):
            success_ratio += 1
        if bool(re.search("Current", text, re.IGNORECASE)):
            success_ratio += 1
        if bool(re.search("TOTAL", text, re.IGNORECASE | re.VERBOSE)):
            success_ratio += 1
        if bool(re.search("Liabilities", text, re.IGNORECASE)):
            success_ratio += 1
        if bool(re.search("receivables", text, re.IGNORECASE)):
            success_ratio += 1
        # print("Ratio : ", success_ratio)
        # print("Page NO : ", pageNo)
        if success_ratio >= 3:
            return pageNo
        pageNo += 1

    return pageNo


# Refine a text
def refineText(arr):
    splittedText1 = []
    splittedText = []
    for t in arr:
        newT = t.strip()
        newT = newT.rstrip()
        newT = newT.lstrip()
        splittedText1.append(newT)
    for t in splittedText1:
        splt_arr = t.split()
        refinedText = ""
        for w in splt_arr:
            newS = w.strip()
            newS = newS.lstrip()
            newS = newS.rstrip()
            refinedText += newS + " "
        refinedText = refinedText.replace(",", "")
        splittedText.append(refinedText.strip())
    return splittedText


# Date Extract
def extract_years(arr):
    years = {
        "current_year": "",
        "previous_year": ""
    }
    year_index = 0
    for line in arr:
        if re.search("note | notes", line, re.IGNORECASE | re.VERBOSE):
            if len(re.findall("\d{4}", line)) == 2:
                years_found = re.findall("\d{4}", line)
                if int(years_found[0]) > int(years_found[1]):
                    years["current_year"] = years_found[0]
                    years["previous_year"] = years_found[1]
                else:
                    years["current_year"] = years_found[1]
                    years["previous_year"] = years_found[0]
    return years


# Current Assets
def current_assets(arr):
    find_curr_counter = 0
    crnt_assets_json = {
        "current_assets": {
            "current_year": None,
            "previous_year": None,
            "receivables": {}
        }
    }
    # Find starting counter of current assets
    for line in arr:
        if re.match("Current\s+assets", line, re.IGNORECASE):
            break
        find_curr_counter += 1
    for index in range(find_curr_counter, len(arr) - 1):
        txt = arr[index]
        txt = txt.replace(" ", "")
        txt = txt.replace(",", "")
        txt = txt.replace(".", "")

        # Find current assets total
        # Find string that contains only numbers and it is our string
        if bool(re.match("^[0-9]+$", txt)):
            # print("Found : ", type(arr[index]))
            # Search for two number pattern ex. '133.33 21312.32' or  '2312312 12312321'
            # Only match for two number pattern because there is always sum of current assets either 0 or more
            if re.match(two_numbers_pattern, arr[index]):
                values = re.findall(two_numbers_pattern, arr[index])
                # print("Values : ", values)
                # Save for current year
                crnt_assets_json["current_assets"]["current_year"] = values[0][0]
                # Save for previous year
                crnt_assets_json["current_assets"]["previous_year"] = values[1][0]
                break

        if re.match(r"total\scurrent\sasset | current\assets\stotal", arr[index], re.IGNORECASE | re.VERBOSE ):
            if re.match(two_numbers_pattern, arr[index]):
                values = re.findall(two_numbers_pattern, arr[index])
                # print("Values : ", values)
                # Save for current year
                crnt_assets_json["current_assets"]["current_year"] = values[0][0]
                # Save for previous year
                crnt_assets_json["current_assets"]["previous_year"] = values[1][0]
                break

        if bool(re.search("receivables", arr[index], re.IGNORECASE)):
            txt = arr[index].split()
            findStr = re.findall("[a-zA-Z]+", arr[index], re.IGNORECASE)
            findStr = "_".join(findStr).lower()
            current_year = txt[len(txt) - 2]
            prev_year = txt[len(txt) - 1]
            if current_year.replace(".", "").isdigit() and prev_year.replace(".", "").isdigit():
                crnt_assets_json["current_assets"]["receivables"][findStr] = {"current_year": current_year,
                                                                              "previous_year": prev_year}
        # Break the loop if following properties found
        if re.match("EQUITIES\sAND\sLIABILITIES", arr[index], re.IGNORECASE):
            break
        if re.match("Non-current\sassets", arr[index], re.IGNORECASE):
            break
        if re.match("LIABILITIES", arr[index], re.IGNORECASE):
            break
        if re.match("EQUITY", arr[index], re.IGNORECASE):
            break

    return crnt_assets_json


# Non Current Assets
def non_current_assets(arr):
    find_non_curr_counter = 0
    non_crnt_assets_json = {
        "non_current_assets": {
            "current_year": None,
            "previous_year": None,
            "receivables": {}
        },
    }
    # Find starting counter of current assets
    for line in arr:
        if re.search("Non\s?-\s?current\s+asset", line, re.IGNORECASE):
            break
        find_non_curr_counter += 1

    for index in range(find_non_curr_counter, len(arr) - 1):
        txt = arr[index]
        txt = txt.replace(" ", "")
        txt = txt.replace(",", "")
        txt = txt.replace(".", "")
        # Find non-current assets total
        # Find string that contains only numbers and it is our string
        if bool(re.match("^[0-9]+$", txt)):
            # print("Found : ", type(arr[index]))
            # Search for two number pattern ex. '133.33 21312.32' or  '2312312 12312321'
            # Only match for two number pattern because there is always sum of non current assets either 0 or more
            if re.match(two_numbers_pattern, arr[index]):
                values = re.findall(two_numbers_pattern, arr[index])
                # print("Values : ", values)
                # Save for current year
                non_crnt_assets_json["non_current_assets"]["current_year"] = values[0][0]
                # Save for previous year
                non_crnt_assets_json["non_current_assets"]["previous_year"] = values[1][0]
                break

        if re.match(r"total\snon\s?-\s?current\sasset | non\s?-\s?current\assets\stotal", arr[index], re.IGNORECASE | re.VERBOSE):
            if re.match(two_numbers_pattern, arr[index]):
                values = re.findall(two_numbers_pattern, arr[index])
                # print("Values : ", values)
                # Save for current year
                non_crnt_assets_json["non_current_assets"]["current_year"] = values[0][0]
                # Save for previous year
                non_crnt_assets_json["non_current_assets"]["previous_year"] = values[1][0]
                break

        if bool(re.search("receivables", arr[index], re.IGNORECASE)):
            txt = arr[index].split()
            findStr = re.findall("[a-zA-Z]+", arr[index], re.IGNORECASE)
            findStr = "_".join(findStr).lower()
            current_year = txt[len(txt) - 2]
            prev_year = txt[len(txt) - 1]
            if current_year.replace(".", "").isdigit() and prev_year.replace(".", "").isdigit():
                non_crnt_assets_json["non_current_assets"]["receivables"][findStr] = {"current_year": current_year,
                                                                                      "previous_year": prev_year}
        # Break the loop if following properties found
        if re.match("EQUITIES\sAND\sLIABILITIES", arr[index], re.IGNORECASE):
            break
        if re.match("current\sassets", arr[index], re.IGNORECASE):
            break
        if re.match("LIABILITIES", arr[index], re.IGNORECASE):
            break
        if re.match("EQUITY", arr[index], re.IGNORECASE):
            break

    return non_crnt_assets_json


# Find total Assets
def find_total_of_all_assets(arr):
    total_assets_counter = 0
    for line in arr:
        if re.match("total\sassets", line, re.IGNORECASE):
            break
        total_assets_counter += 1

    for index in range(total_assets_counter, total_assets_counter + 5):
        if re.match("total\sassets", arr[index], re.IGNORECASE):
            values = re.findall(two_numbers_pattern, arr[index])
            return {"total_assets": {"current_year": values[0][0], "previous_array": values[1][0]}}


# current Liabilities
def current_liabilities(arr):
    find_curr_counter = 0
    crnt_liabilities_json = {
        "current_liabilities": {
            "current_year": None,
            "previous_year": None,
            "payables": {}
        }
    }
    # Find starting counter of current assets
    for line in arr:
        if re.match("Current\s+liabilities", line, re.IGNORECASE):
            break
        find_curr_counter += 1

    for index in range(find_curr_counter, len(arr) - 1):
        txt = arr[index]
        txt = txt.replace(" ", "")
        txt = txt.replace(",", "")
        txt = txt.replace(".", "")
        if bool(re.match("^[0-9]+$", txt)):
            # print("Found : ", type(arr[index]))
            # Search for two number pattern ex. '133.33 21312.32' or  '2312312 12312321'
            # Only match for two number pattern because there is always sum of non current assets either 0 or more
            if re.match(two_numbers_pattern, arr[index]):
                values = re.findall(two_numbers_pattern, arr[index])
                # print("Values : ", values)
                # Save for current year
                crnt_liabilities_json["current_liabilities"]["current_year"] = values[0][0]
                # Save for previous year
                crnt_liabilities_json["current_liabilities"]["previous_year"] = values[1][0]
                break
        if bool(re.search("payables", arr[index], re.IGNORECASE)):
            txt = arr[index].split()
            findStr = re.findall("[a-zA-Z]+", arr[index], re.IGNORECASE)
            findStr = "_".join(findStr).lower()
            current_year = txt[len(txt) - 2]
            prev_year = txt[len(txt) - 1]
            if current_year.replace(".", "").isdigit() or current_year == "- " and prev_year.replace(".", "").isdigit():
                crnt_liabilities_json["current_liabilities"]["payables"][findStr] = {"current_year": current_year,
                                                                                     "previous_year": prev_year}
        # if re.match("non-Current\sliabilities", arr[index], re.IGNORECASE | re.VERBOSE):
        #     print("BreakPoint : ", arr[index])
        #     break
        if re.match(r"TOTAL\sEQUITY\s | TOTAL\sEQUITY\sand\sliabilities", arr[index], re.IGNORECASE | re.VERBOSE):
            # print("BreakPoint yoo : ", arr[index])
            break
    #
    # print(arr[find_curr_counter])
    return crnt_liabilities_json


# Non current liabilities
def non_current_liabilities(arr):
    find_curr_counter = 0
    non_crnt_liabilities_json = {
        "non_current_liabilities": {
            "current_year": None,
            "previous_year": None,
            "payables": {}
        }
    }
    # Find starting counter of current assets
    for line in arr:
        if re.match("Non\s?-\s?current\sliabilities", line, re.IGNORECASE):
            break
        find_curr_counter += 1

    for index in range(find_curr_counter, len(arr) - 1):
        txt = arr[index]
        txt = txt.replace(" ", "")
        txt = txt.replace(",", "")
        txt = txt.replace(".", "")
        if bool(re.match("^[0-9]+$", txt)):
            # print("Found : ", type(arr[index]))
            # Search for two number pattern ex. '133.33 21312.32' or  '2312312 12312321'
            # Only match for two number pattern because there is always sum of non current assets either 0 or more
            if re.match(two_numbers_pattern, arr[index]):
                values = re.findall(two_numbers_pattern, arr[index])
                # print("Values : ", values)
                # Save for current year
                non_crnt_liabilities_json["non_current_liabilities"]["current_year"] = values[0][0]
                # Save for previous year
                non_crnt_liabilities_json["non_current_liabilities"]["previous_year"] = values[1][0]
                break
        if bool(re.search("payables", arr[index], re.IGNORECASE)):
            txt = arr[index].split()
            findStr = re.findall("[a-zA-Z]+", arr[index], re.IGNORECASE)
            findStr = "_".join(findStr).lower()
            current_year = txt[len(txt) - 2]
            prev_year = txt[len(txt) - 1]
            if current_year.replace(".", "").isdigit() and prev_year.replace(".", "").isdigit():
                non_crnt_liabilities_json["non_current_liabilities"]["payables"][findStr] = {
                    "current_year": current_year,
                    "previous_year": prev_year}
        # if re.match("non-Current\sliabilities", arr[index], re.IGNORECASE | re.VERBOSE):
        #     print("BreakPoint : ", arr[index])
        #     break
        if re.match(r"TOTAL\sEQUITY\s | TOTAL\sEQUITY\sand\sliabilities", arr[index], re.IGNORECASE | re.VERBOSE):
            # print("BreakPoint yoo : ", arr[index])
            break
    return non_crnt_liabilities_json


def get_equity(arr):
    equity_counter = 0
    equity = {}
    for line in arr:
        if re.match("equity", line, re.IGNORECASE):
            break
        equity_counter += 1

    for index in range(equity_counter, equity_counter + 10):
        if bool(re.match("share\s+capital", arr[index], re.IGNORECASE)):
            # print(arr[index])
            txt = arr[index].split()
            findStr = re.findall("[a-zA-Z]+", arr[index], re.IGNORECASE)
            findStr = "_".join(findStr).lower()
            current_year = txt[len(txt) - 2]
            prev_year = txt[len(txt) - 1]
            if current_year.replace(".", "").isdigit() and prev_year.replace(".", "").isdigit():
                equity["share_capital"] = {"current_year": current_year, "previous_year": prev_year}

    return equity


def parsePdf(file):
    page = get_page_no(file)
    if page == len(file.pages):
        return 0

    balanceSheetPage = file.pages[page]
    refinedArr = refineText(balanceSheetPage.extract_text().splitlines())
    years = extract_years(refinedArr)
    # Assets functions
    current_asset_total = current_assets(refinedArr)
    non_current_assets_total = non_current_assets(refinedArr)
    total_assets = find_total_of_all_assets(refinedArr)
    # Liabilities functions
    current_liabilities_total = current_liabilities(refinedArr)
    non_current_liabilities_total = non_current_liabilities(refinedArr)
    # Share capital
    share_capital = get_equity(refinedArr)
    json_data = {
        "years": years,
        "assets": {
            "current_assets": current_asset_total,
            "non_current_assets": non_current_assets_total,
            "total_assets": total_assets
        },
        "liabilities": {
            "current_liabilities": current_liabilities_total,
            "non_current_liabilities": non_current_liabilities_total
        },
        "equity": {
            "share_capital": share_capital
        }
    }

    print(json.dumps(json_data))

parsePdf(file)
