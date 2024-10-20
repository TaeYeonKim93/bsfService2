import axios from 'axios';

export interface Landmark {
  pageid: number;
  title: string;
  lat: number;
  lon: number;
  description: string;
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
        gslimit: 10,
        format: 'json',
        origin: '*',
      },
    });

    const landmarks: Landmark[] = response.data.query.geosearch.map((item: any) => ({
      pageid: item.pageid,
      title: item.title,
      lat: item.lat,
      lon: item.lon,
      description: '',
      wikipediaUrl: `https://en.wikipedia.org/?curid=${item.pageid}`,
    }));

    // Fetch descriptions for each landmark
    await Promise.all(
      landmarks.map(async (landmark) => {
        const descriptionResponse = await axios.get(WIKIPEDIA_API_URL, {
          params: {
            action: 'query',
            pageids: landmark.pageid,
            prop: 'extracts',
            exintro: true,
            explaintext: true,
            format: 'json',
            origin: '*',
          },
        });

        landmark.description = descriptionResponse.data.query.pages[landmark.pageid].extract.slice(0, 200) + '...';
      })
    );

    return landmarks;
  } catch (error) {
    console.error('Error fetching landmarks:', error);
    return [];
  }
}
