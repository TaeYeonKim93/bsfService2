import axios from 'axios';

interface AddressSearchResult {
  roadAddr: string;
  roadAddrPart1: string;
  roadAddrPart2: string;
  jibunAddr: string;
  engAddr: string;
  zipNo: string;
  admCd: string;
  rnMgtSn: string;
  bdMgtSn: string;
  detBdNmList: string;
  bdNm: string;
  bdKdcd: string;
  siNm: string;
  sggNm: string;
  emdNm: string;
  liNm: string;
  rn: string;
  udrtYn: string;
  buldMnnm: string;
  buldSlno: string;
  mtYn: string;
  lnbrMnnm: string;
  lnbrSlno: string;
  emdNo: string;
}

export async function searchAddress(keyword: string): Promise<AddressSearchResult[]> {
  try {
    const response = await axios.get('https://business.juso.go.kr/addrlink/addrLinkApiJsonp.do', {
      params: {
        confmKey: process.env.JUSO_API_KEY, // We'll use an environment variable for the API key
        currentPage: 1,
        countPerPage: 10,
        keyword: keyword,
        resultType: 'json'
      },
      adapter: require('axios/lib/adapters/http')
    });

    // Extract the JSON from the JSONP response
    const jsonStr = response.data.replace(/^\(/, '').replace(/\)$/, '');
    const data = JSON.parse(jsonStr);

    if (data.results.common.errorCode !== '0') {
      throw new Error(data.results.common.errorMessage);
    }

    return data.results.juso;
  } catch (error) {
    console.error('Error searching address:', error);
    throw error;
  }
}
