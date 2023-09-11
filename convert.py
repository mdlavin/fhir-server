import requests
import json
from urllib.parse import quote_plus 
import re
import uuid
import jmespath
from lenses import lens
from progress.bar import Bar
import argparse
import os

parser = argparse.ArgumentParser(description='Convert CCDA to FHIR and import it')
parser.add_argument('file', metavar='FILE', type=str, help='The CCDA file to import')
parser.add_argument('--account', metavar='ACCOUNT', type=str, help='The LifeOmic account to import into')
parser.add_argument('--project', metavar='PROJECT', type=str, help='The LifeOmic project ID to import into')
parser.add_argument('--pull', action='store_true', help='Whether to pull the CCDA file from LifeOmic')

# Read the environment variable API_KEY
API_KEY = os.environ.get('API_KEY')

args = parser.parse_args()

local_ccda_file = args.file
if args.pull:
	download_start_resp = requests.get('https://api.us.lifeomic.com/v1/files/' + args.file + '?include=downloadUrl', headers={
		'LifeOmic-Account': args.account,
		'Authorization': 'Bearer ' + API_KEY
	})
	download_json = download_start_resp.json()
	print(download_json)
	r = requests.get(download_json['downloadUrl'])  
	temp_filename = 'ccda.xml'
	with open(temp_filename, 'wb') as f:
		f.write(r.content)
	local_ccda_file = temp_filename

#Read file as text into variable
with open(local_ccda_file, 'r') as file:
    inputData = file.read()

project_id = args.project
account = args.account

# The local FHIR server URL
url = "http://localhost:8080/" + quote_plus("$convert-data")
body = {
    "resourceType": "Parameters",
    "parameter": [
        {
            "name": "inputData",
            "valueString": inputData,
        },
        {
            "name": "inputDataType",
            "valueString": "Ccda"
        },
        {
            "name": "templateCollectionReference",
            "valueString": "microsofthealth/ccdatemplates:default"
        },
        {
            "name": "rootTemplate",
            "valueString": "CCD"
        }
    ]
}

response = requests.post(url, json=body)

response_text = response.text

# The LifeOmic platform requires that all UUIDs be v4 UUIDs
# This logic converts them to v4 UUIDs
uuid_pattern = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
uuids = set(re.findall(uuid_pattern, response_text))
for old_uuid in uuids:
	print("Replacing", old_uuid)
	new_uuid = str(uuid.uuid4())
	response_text = response_text.replace(old_uuid, new_uuid)

entries = json.loads(response_text)['entry']

GLUCOSE = {
	'code':'6749-6',
	'allowed_units': ['mg/dL'],
}

WBC = {
	'code':'6690-2',
	'allowed_units': ['K/uL', 'Thousand/uL', 'x10E3/uL', '10*3/ul'],
	'canonical_unit': '10*3/uL'
}

MCV = {
	'code':'787-2',
	'allowed_units': ['fL', 'fl']
}

RDW = {
	'code':'788-0',
	'allowed_units': ['%']
}

HEMOGLOBIN = {
	'code':'718-7',
	'allowed_units': ['g/dL']
}

ALT = {
	'code':'1742-6',
	'allowed_units': ['IU/L', 'U/L'],
	'canonical_unit': 'U/L'
}

AST = {
	'code':'30239-8',
	'allowed_units': ['IU/L', 'U/L'],
	'canonical_unit': 'U/L'
}

ALBUMIN = {
	'code':'1751-7',
	'allowed_units': ['g/dL'],
}

AMMONIA = {
	'code':'32664-5',
	'allowed_units': ['umol/L'],
}


PLATELETS = {
	'code':'777-3',
	'allowed_units': ['K/uL', 'Thousand/uL', 'x10E3/uL', '10*3/ul'],
	'canonical_unit': '10*3/uL'
}

DHEA_SULFATE = {
	'code': '2191-5',
	'allowed_units': ['mcg/dL'],
}

ESTRADIOL = {
	'code': '2243-4',
	'allowed_units': ['pg/mL'],
}

GGT = {
	'code': '2324-2',
	'allowed_units': ['U/L'],
}

HOMOCYSTEINE = {
	'code': '13965-9',
	'allowed_units': ['umol/L'],
}


PSA_TOTAL = {
	'code': '2857-1',
	'allowed_units': ['ng/mL'],
}

SEX_HORMONE_BINDING_GLOBULIN = {
	'code': '13967-5',
	'allowed_units': ['nmol/L'],
}

TESTOSTERONE_FREE = {
	'code': '2991-8',
	'allowed_units': ['pg/mL'],
}

TESTOSTERONE_TOTAL_MS = {
	'code': '2986-8',
	'allowed_units': ['ng/dL'],
}

CHOL_HDL_RATIO = {
	'code':'9830-1',
	'allowed_units': ['(calc)', 'calc'],
	'canonical_unit': 'calc',
}

TOTAL_CHOLESTEROL = {
	'code':'2093-3',
	'allowed_units': ['mg/dL'],
}

LDL_CHOLESTEROL = {
	'code':'13457-7',
	'allowed_units': ['mg/dL_(calc)'],
}

HDL_CHOLESTEROL = {
	'code':'2085-9',
	'allowed_units': ['mg/dL'],
}

NON_HDL_CHOLESTEROL = {
	'code':'43396-1',
	'allowed_units': ['mg/dL_(calc)'],
}

TRICLYCERIDES = {
	'code':'2571-8',
	'allowed_units': ['mg/dL'],
}

INSULIN = {
	'code':'20448-7',
	'allowed_units': ['uIU/mL'],
}

FERRITIN = {
	'code':'2276-4',
	'allowed_units': ['ng/mL'],
}

MAGNESIUM = {
	'code':'19123-9',
	'allowed_units': ['mg/dL'],
}

LH = {
	'code':'10501-5',
	'allowed_units': ['mIU/mL'],
}


DISPLAY_NAME_TO_CODE = {
	"AST (SGOT)": AST,
	"AST": AST,
	"ALT (SGPT)": ALT,
	"ALT": ALT,
	"Albumin [Mass/volume] in Serum or Plasma": ALBUMIN,
	"Albumin": ALBUMIN,
	"ALBUMIN": ALBUMIN,
	"Ammonia": AMMONIA,
	"Hemoglobin [Mass/volume] in Blood": HEMOGLOBIN,
	'HEMOGLOBIN': HEMOGLOBIN,
	"Hemoglobin": HEMOGLOBIN,
	"PLATELET COUNT": PLATELETS,
	"Platelets": PLATELETS,
	"RDW": RDW,
	"WBC  (CLH 0370)": WBC,
	"WHITE BLOOD CELL COUNT":  WBC,
	"WBC": WBC,
	"White Blood Cells": WBC,
	"MCV": MCV,
	"GLUCOSE": GLUCOSE,
	"Glucose": GLUCOSE,

	"General Comments & Additional Information": {
		'code': '77202-0',
		'allowed_units': [],
	},
	"VITAMIN B12": {
		'code': '14685-2',
		'allowed_units': ['pg/mL'],
	},
	"FOLATE, SERUM": {
		'code': '2284-8',
		'allowed_units': ['ng/mL'],
	},
	"URIC ACID": {
		'code': '3084-1',
		'allowed_units': ['mg/dL'],
	},
	'LDL/HDL RATIO': {
		'code': '11054-4',
		'allowed_units': ['(calc)', 'calc'],
		'canonical_unit': 'calc',
	},
	"DHEA SULFATE (SO4)": DHEA_SULFATE,
	"DHEA SULFATE": DHEA_SULFATE,
	"ESTRADIOL": ESTRADIOL,
	"Estradiol": ESTRADIOL,
	"G-Glutamyltransferase": GGT,
	"GGT": GGT,
	"HOMOCYSTEINE": HOMOCYSTEINE,
	"Homocyst(e)ine": HOMOCYSTEINE,
	"PSA, TOTAL": PSA_TOTAL,
	"PSA, Total": PSA_TOTAL,
	"SEX HORMONE BINDING GLOBULIN": SEX_HORMONE_BINDING_GLOBULIN,
	"TESTOSTERONE, FREE": TESTOSTERONE_FREE,
	"TESTOSTERONE, TOTAL, MS": TESTOSTERONE_TOTAL_MS,
	"CHOL/HDLC RATIO": CHOL_HDL_RATIO,
	"CHOLESTEROL, TOTAL": TOTAL_CHOLESTEROL,
	"HDL CHOLESTEROL": HDL_CHOLESTEROL,
	"LDL-CHOLESTEROL": LDL_CHOLESTEROL,
	"NON HDL CHOLESTEROL": NON_HDL_CHOLESTEROL,
	"TRIGLYCERIDES": TRICLYCERIDES,
	"Trig": TRICLYCERIDES,
	"INSULIN": INSULIN,
	"FERRITIN": FERRITIN,
	"MAGNESIUM": MAGNESIUM,
	"LH": LH,
	"LD": {
		'code': '14804-9',
		'allowed_units': ['IU/L', 'U/L'],
	},
	'PROLACTIN': {
		'code': '2842-3',
		'allowed_units': ['ng/mL'],
	},
	'LIPOPROTEIN (a)': {
		'code': '43583-4',
		'allowed_units': ['nmol/L'],
	}
}

def optionalGet(key):
	def folder(state):
		if key in state:
			yield state[key]
	
	def builder(state, values):
		if len(values) > 1:
			raise Exception('Cannot set multiple values')
		if key in state:
			if len(values) < 1:
				raise Exception('Not enough values')
			state[key] = values[0]
			return state
		else:
			if len(values) > 0:
				raise Exception('Cannot set a value that did not previously exist')

	return lens.Traversal(folder, builder)

def concatTraversals(traversals):
	def folder(state):
		for traversal in traversals:
			values = traversal.collect()(state)
			for value in values: yield value
	
	def builder(state, values):
		for traversal in traversals:
			old_values = traversal.collect()(state)
			new_values = values[:len(old_values)] 
			state = traversal.set_many(new_values)(state)
			values = values[len(old_values):]
		return state


	return lens.Traversal(folder, builder)

valueUnit = optionalGet('valueQuantity') & optionalGet('unit')
referenceUnits = optionalGet('referenceRange').Each() & concatTraversals([
	(optionalGet('low') & optionalGet('unit')),
	(optionalGet('high') & optionalGet('unit'))
])
allUnits = concatTraversals([valueUnit, referenceUnits])

medicationReference = optionalGet('medicationReference') & optionalGet('reference')
medicationCodes = (optionalGet('code') & optionalGet('coding')).Each()

progress = Bar('Importing', max=len(entries))
for entry in entries:
	progress.next()
	resource = entry['resource']
	type = resource['resourceType']
	if type == 'AllergyIntolerance': continue

	meta = resource.get('meta', {})
	tag = meta.get('tag', [])
	tag.append({
		"system": "http://lifeomic.com/fhir/dataset",
		"code": project_id
	})
	meta['tag'] = tag
	resource['meta'] = meta

	if type == 'MedicationStatement':
		reference = medicationReference.collect()(resource)
		if len(reference):
			reference = reference[0]
			medication = next(filter(lambda entry: entry['request']['url'] == reference, entries))
			codes = medicationCodes.collect()(medication['resource'])
			resource['medicationCodeableConcept'] = {
				'coding': codes
			}

	if type == 'Observation':
		coding = jmespath.search('code.coding[0]', resource); 
		if coding.get('system') == 'http://loinc.org' and coding.get('code') == '77202-0':
			fixed_code = DISPLAY_NAME_TO_CODE.get(coding['display'])

			if not fixed_code:
				print("No code for", coding['display'])

			# Find all references to units in the observation and 
			# collect them into a list
			units = allUnits.collect()(resource)

			if fixed_code:
				if all(unit in fixed_code['allowed_units'] for unit in units):
					resource['code']['coding'][0]['code'] = fixed_code['code']
					if 'canonical_unit' in fixed_code:
						# Update all units with the canonical unit
						resource = allUnits.set(fixed_code['canonical_unit'])(resource)

				else:
					print("Skipping", resource, fixed_code['allowed_units'])
					pass


	response = requests.put('https://fhir.us.lifeomic.com/' + account + '/dstu3/' + entry['request']['url'], json=resource, headers={
		'Content-Type': 'application/json',
		'Authorization': 'Bearer ' + API_KEY
	})
	if response.status_code != 200 and response.status_code != 201:
		print(response.status_code)
		print(response.text)
		raise Exception('Failed to create resource')

progress.finish()

print(',\n'.join(DISPLAY_NAME_TO_CODE.keys()))