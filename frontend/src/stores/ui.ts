import { create } from "zustand"

const DEPARTMENTS = [
  "All",
  "Revenue",
  "Home",
  "Law",
  "Transport",
  "Education",
  "Health",
  "Urban Development",
  "Rural Development",
  "Forest",
  "Other",
] as const

type Department = (typeof DEPARTMENTS)[number]

interface UIState {
  department: Department
  departments: readonly Department[]
  setDepartment: (department: Department) => void
  restore: () => void
}

export const useUIStore = create<UIState>((set) => ({
  department: "All",
  departments: DEPARTMENTS,
  setDepartment: (department) => {
    set({ department })
  },
  restore: () => set({ department: "All" }),
}))
