import axios from 'axios';

export interface Landmark {
  pageid: number;
  title: string;
  lat: number;
  lon: number;
  wikipediaUrl: string;
}

const WIKIPEDIA_API_URL = 'https://en.wikipedia.org/w/api.php';

export async function fetchLandmarks(south: number, west: number, north: number, east: number): Promise<Landmark[]> {
  try {
    const response = await axios.get(WIKIPEDIA_API_URL, {
      params: {
        action: 'query',
        list: 'geosearch',
        gscoord: `${(north + south) / 2}|${(east + west) / 2}`,
        gsradius: 10000,
        gslimit: 5,
        format: 'json',
        origin: '*',
      },
    });

    const landmarks: Landmark[] = response.data.query.geosearch.map((item: any) => ({
      pageid: item.pageid,
      title: item.title,
      lat: item.lat,
      lon: item.lon,
      wikipediaUrl: `https://en.wikipedia.org/?curid=${item.pageid}`,
    }));

    return landmarks;
  } catch (error) {
    console.error('Error fetching landmarks:', error);
    return [];
  }
}
