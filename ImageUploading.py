import requests
import base64
import json
import os

ALLOWED_CATEGORY = "Test upload"
API_KEY = "06Q9CLAC8D69ECGB80AL"
known_dict = {
'categories': ['Chris Test', 'General', '2016 PAD VALIDATION', '2017 Laos preparation', '2015-2016 USAID DIV project', 'FHI360', 'Chemo Drugs'], 'samples': ['Acetaminophen', 'Acetylsalicylic Acid', 'Amodiaquine', 'Amoxicillin', 'Ampicillin', 'Artesunate', 'Azithromycin', 'Borate', 'Calcium Carbonate', 'Calcium Sulfate', 'Chloramphenicol', 'Chloroquine', 'Ciprofloxacin', 'Corn Starch', 'DI water', 'Diethylcarbamazine', 'Dihydoartemisinin', 'Doxycycline', 'Dried Wheat Starch', 'Erythromycin', 'Ethambutol', 'Furosemide', 'Isoniazid', 'Levofloxacin', 'Lumefantrine', 'Metformin', 'Oseltamivir', 'Penicillin G', 'Polyethylene Glycol', 'Potato Starch', 'Primaquine', 'Pyrazinamide', 'Quinine', 'Quinine Sulfate', 'Rifampicin', 'Streptomycin', 'Sulfadoxine', 'Talc', 'Tetracycline', 'Tryptophan', 'epinephrine', 'MgSO4', 'mebendazole', 'albendazole', 'glucose', 'caffeine', 'Dapsone', 'Artemether', 'Ceftriaxone injectable', 'Ceftriaxone', 'Cefuroxime', 'Cephalexin', 'Tap water', 'Enalapril', 'Losartan', 'Amoxycillin clavulonic acid', 'Sweet Rice', 'Lake Water', 'RHZE', 'NaH2PO4', 'Na2HPO4', 'K3PO4', 'K2HPO4', 'KH2PO4', 'Na3PO4', 'Kenya Amoxycillin Dosage Forms', 'amoxyclav', 'Clavulanate, lithium salt (USP standard)', 'Cefuroxime Axetil', 'Amoxicillin rerun', 'Pyrazinamide rerun', 'EthIso', 'Rifiso', 'Unknown', 'Sildenafil', 'Chlorpheniramine Maleate', 'Bad Amoxicillin', 'Amoxicillin Kenya Companies', 'Amoxyclav Kenya Companies', 'Dihydroartimisinin Piperaquine Dosage Form', 'Sulfamethoxazole Trimethoprim Dosage Form', 'hydralazine hydrochloride', 'hydrochlorothiazid', 'ofloxacin API', 'ofloxacin dosage form', 'pyrimethamine', 'trimethoprim', 'sulfanilamide', 'sulfamethoxazole', 'Cocaine', 'Methamphetamine', 'Heroin', 'Water', 'Lactose', 'Tramadol', 'Dimethylsulfone', 'Fentanyl Mix', 'Crack Cocaine', 'Aderall', 'Cocaine HCl', 'DEC', 'Indole', 'Lidocaine', 'Benzocaine', 'Procaine', 'Butane Honey Oil', 'MDMA', 'Dimethyl Sulfone', 'Chloral Hydrate', 'Diazapam', 'Peyote Cactus', 'NQS'], 'tests': ['Acidic Cobalt Thiocyanate', 'Aspirin Test', 'Basic Cobalt Thiocyanate', 'Beta-lactam (Cu)', 'Biuret', 'Carbonate', 'Dimethylcinnamonaldehyde (DMCA)', 'Eosine Red', 'Eriochrome Black T K2CO3', 'Eriochrome Black T NaOH', 'Ethambutol (Cu)', 'Hemin', 'Iron (III) Chloride-Carbonate Test', 'Magic SNP', 'Naphthaquinone Sulfonate (NQS)', 'Ninhydrin', 'Nirophenols-HONO', 'Phenols-HONO and PNA', 'Pyridyl Pyridinium Chloride (PPC)', 'Rimani Test', 'Sodium Nitroprusside (SNP)', 'Timer', 'Triiodide Povidone', 'Turmeric', '12 Lane PAD Kenya 2014', 'SaltPAD', 'amPAD_Early', 'amPAD_Late', 'Sandipan1', '12LanePADKenya2015', 'dropbox', 'Lane G (SNP) for Clav standards', 'HPLC Comparison', '2017 Laos Antibiotic PAD', 'idPAD', 'chemoPAD']}

def getBriefData(category):
  known_values = known_dict[category]
  ret = list(known_values)
  return ret

def getData(category):
  url = "https://pad.crc.nd.edu/index.php"
  values = {
    "queryname": category,
    "option": "com_jbackend",
    "view": "request",
    "api_key": API_KEY,
    "module": "querytojson",
    "resource": "list",
    "action": "get"
    }
  response = requests.get(url, values)
  data = response.json()
  ret = []
  if json.dumps(data['status']) == '"ok"':
    data = json.dumps(data['list'])
    data = json.loads(data)
    for i in range(len(data)):
      temp = json.dumps(data[i])[2:][:-2]
      ret.append(temp)
  known_values = known_dict[category]
  ret = set(ret).union(set(known_values))
  ret = list(ret)
  return ret

def postData(file1, file2, sample, test, category, idnum):
  print("Posting...")
  f = open(file1, "r")
  data = f.read()
  f2 = open(file2, "r")
  data2 = f2.read()
  encodeData = base64.b64encode(data)
  encodeData2 = base64.b64encode(data2)
  url = "https://pad.crc.nd.edu/index.php"
  values = {
    "option": "com_jbackend",
    "view": "request",
    "api_key": API_KEY,
    "module": "querytojson",
    "resource": "upload",
    "action": "post",
    "sample_name": sample,
    "test_name": test,
    "category_name": category,
    "camera1": "RaspberryPi",
    "notes": "testing",
    "file_name2": "raw.png",
    "file_name": "processed.png",
    "sampleid": idnum,
    "uploaded_file2": encodeData,
    "uploaded_file": encodeData2
  }
  response = requests.post(url, values)
  ret = response.json()
  print("Done posting")
  return json.dumps(ret['status']) == '"ok"'

def getPred(idnum):
  url = "https://pad.crc.nd.edu/index.php"
  values = {
    "option": "com_jbackend",
    "view": "request",
    "api_key": API_KEY,
    "module": "querytojson",
    "resource": "list",
    "action": "get",
    "queryname": "predict",
    "serialnumber": idnum
  }
  response = requests.get(url, values)
  ret = response.json()
  print(json.dumps(ret))


def uploadFormatedDir(directory, src="/PAD_Data/", dst="/Uploaded_PADs/"):
  rootDirectory = os.path.dirname(directory)
  tempDirectory = rootDirectory + src
  padDirectory = rootDirectory + dst
  if not os.path.exists(tempDirectory):
    return
  if not os.path.exists(padDirectory):
    os.mkdir(padDirectory)
  for pad in os.listdir(tempDirectory):
    if not pad.startswith("."):
      if not os.path.exists(padDirectory+pad):
        os.mkdir(padDirectory+pad)
      for sample in os.listdir(tempDirectory+pad):
        if not sample.startswith("."):
          print("Uploading", pad)
          uploadSample(tempDirectory+pad+"/"+sample, pad)
          os.rename(tempDirectory+pad+"/"+sample, padDirectory+pad+"/"+sample)
        else:
          os.remove(tempDirectory+pad+"/"+sample)
      os.rmdir(tempDirectory+pad)
    else:
      os.remove(tempDirectory+pad)
  os.rmdir(tempDirectory)

def uploadSample(sample, pad):
      data = getMetadata(sample+"/data.json")
      print(data)
      sample_data = data["sample_name"]
      test = data["test_name"]
      category = data["category_name"]
      raw = sample+"/raw.jpg"
      processed = sample+"/processed.jpg"
      success = postData(raw, processed, sample_data, test, category, pad)
      data["uploaded"] = success
      writeMetadata(sample+"/data.json", data)

def getMetadata(directory):
  sourceFile = open(directory, 'r')
  data = sourceFile.read()
  return(json.loads(data)[0])

def writeMetadata(directory, data):
  dstFile = open(directory, 'w')
  json.dump([data], dstFile)


if __name__ == '__main__':
  print(getData('samples'))