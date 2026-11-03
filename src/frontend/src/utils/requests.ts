/**
 *  This is a helper function made to reduce boilerplate code that usually accompanies 
 *  API requests. It uses POST as the default method, so in use you can just call it 
 *  like this: const response = apiRequest(url, payload) - where url is the api address 
 *  and payload is a JSON object e.g. const payload = {file_ref: 'MyFile.csv'}.
 */

export async function apiRequest(
  url: string,
  payload: any = {},
  method: string = "POST", // POST as the default as it is the most commonly used in the Suite
  options: { signal?: AbortSignal } = {}
) {
  const baseOptions: RequestInit = {
    method,
    credentials: "include", // This is needed to ensure cookies are sent (in particular, our session_id cookie)
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json",
    },
    signal: options.signal,
  };

  const requestOptions: RequestInit =
    method !== "GET"
      ? {
        ...baseOptions,
        body: JSON.stringify(payload),
      }
      : baseOptions;

  try {
    const res = await fetch(url, requestOptions);

    if (!res.ok) {
      let message = `HTTP ${res.status}`;

      try {
        const errorData = await res.json();
        if (errorData?.detail) {
          message = errorData.detail;
        }
      } catch {
        // response was not JSON — ignore
      }

      throw new Error(message);
    }


    return await res.json();
  } catch (err: any) {

    if (err.name === "AbortError") {
      throw err;
    }

    console.error(`${method} error:`, err);
    throw err;
  }
}
