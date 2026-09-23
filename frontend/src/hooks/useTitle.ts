import { useEffect } from "react";

export function useTitle(title: string) {
  useEffect(() => {
    document.title = title === "Orbit" ? "Orbit" : `${title} · Orbit`;
  }, [title]);
}
