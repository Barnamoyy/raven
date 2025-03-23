/* eslint-disable @typescript-eslint/no-explicit-any */
import { create } from "zustand";
import { persist, PersistStorage } from "zustand/middleware";
import { get, set, del } from "idb-keyval";

// ✅ IndexedDB Custom Storage
const indexedDBStorage: PersistStorage<any> = {
  getItem: async (name) => {
    const value = await get(name);
    return value ?? null; // Ensure `null` is returned instead of `undefined`
  },
  setItem: async (name, value) => {
    await set(name, value);
  },
  removeItem: async (name) => {
    await del(name);
  },
};

// ✅ Zustand Store
interface DataState {
  latest: any | null; // Only serializable data stored
  setLatest: (data: any) => void; // Function not stored
}

export const useDataStore = create<DataState>()(
  persist(
    (set) => ({
      latest: null,
      setLatest: (data) => set({ latest: data }), // Function stays in-memory
    }),
    {
      name: "data-store",
      storage: indexedDBStorage, // ✅ Uses IndexedDB for serializable data
      partialize: (state) => ({ latest: state.latest }), // ✅ Only store `latest`
    }
  )
);
