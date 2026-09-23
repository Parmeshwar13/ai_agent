export type StartingPoint = {
  id: string;
  name: string;
  summary: string;
  description: string;
};

export const startingPoints: StartingPoint[] = [
  {
    id: "clinic",
    name: "Clinic scheduling",
    summary: "Appointments for independent clinics.",
    description:
      "Build a scheduling product for independent clinics. Front desk staff book appointments, clinicians see a daily roster, and patients receive reminders. Include role-based access and an audit log. Do not assume a particular web framework.",
  },
  {
    id: "bindery",
    name: "Bindery commerce",
    summary: "Orders and quotes for bookbinders.",
    description:
      "Build a small commerce product for independent bookbinders. Customers request quotes, binders track jobs, and the shop publishes a catalog. Payments can be recorded manually at first. Keep the product separate from any other Orbit project.",
  },
  {
    id: "dispatch",
    name: "Field dispatch",
    summary: "Work orders for a utilities contractor.",
    description:
      "Build a field-service product for a utilities contractor. Dispatchers assign work orders, technicians update status from a phone, and supervisors review completion notes. Include shifts, permissions, and a daily report. The stack should be chosen later from the requirements, not assumed now.",
  },
];
