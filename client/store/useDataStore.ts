import { create } from "zustand";
import { persist } from "zustand/middleware";


interface DataState {
  latest: any | null; // Store the latest response globally
  setLatest: (data: any) => void; // Function to update latest response
}


export const useDataStore = create<DataState>()(
    persist(
      (set) => ({
        latest: null,
        setLatest: (data) => set({ latest: data }),
      }),
      {
        name: "data-store", // LocalStorage key
      }
    )
  );
