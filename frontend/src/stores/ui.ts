import { create } from "zustand"

const DEPARTMENTS = [
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
  department: "Revenue",
  departments: DEPARTMENTS,
  setDepartment: (department) => {
    localStorage.setItem("department", department)
    set({ department })
  },
  restore: () => {
    const saved = localStorage.getItem("department")
    if (saved && DEPARTMENTS.includes(saved as Department)) {
      set({ department: saved as Department })
    }
  },
}))
