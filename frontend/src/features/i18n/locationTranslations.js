// Display-only labels. Form values and API payloads continue to use the
// canonical English/code values returned by the location service.
const DISTRICTS = {
  Angul: "ଅନୁଗୁଳ", Balangir: "ବଲାଙ୍ଗିର", Balasore: "ବାଲେଶ୍ୱର", Bargarh: "ବରଗଡ଼",
  Baudh: "ବୌଦ୍ଧ", Boudh: "ବୌଦ୍ଧ", Bhadrak: "ଭଦ୍ରକ", Cuttack: "କଟକ",
  Deogarh: "ଦେବଗଡ଼", Dhenkanal: "ଢେଙ୍କାନାଳ", Gajapati: "ଗଜପତି", Ganjam: "ଗଞ୍ଜାମ",
  Jagatsinghpur: "ଜଗତସିଂହପୁର", Jajpur: "ଯାଜପୁର", Jharsuguda: "ଝାରସୁଗୁଡ଼ା",
  Kalahandi: "କଳାହାଣ୍ଡି", Kandhamal: "କନ୍ଧମାଳ", Kendrapara: "କେନ୍ଦ୍ରାପଡ଼ା",
  Kendujhar: "କେନ୍ଦୁଝର", Keonjhar: "କେନ୍ଦୁଝର", Khordha: "ଖୋର୍ଦ୍ଧା", Khurda: "ଖୋର୍ଦ୍ଧା",
  Koraput: "କୋରାପୁଟ", Malkangiri: "ମାଲକାନଗିରି", Mayurbhanj: "ମୟୂରଭଞ୍ଜ",
  Nabarangpur: "ନବରଙ୍ଗପୁର", Nayagarh: "ନୟାଗଡ଼", Nuapada: "ନୂଆପଡ଼ା",
  Puri: "ପୁରୀ", Rayagada: "ରାୟଗଡ଼", Sambalpur: "ସମ୍ବଲପୁର", Subarnapur: "ସୁବର୍ଣ୍ଣପୁର",
  Sonepur: "ସୁବର୍ଣ୍ଣପୁର",
};

export function locationDisplayName(value, locale) {
  if (!value || locale !== "or-IN") return value;
  return DISTRICTS[value] || value;
}
