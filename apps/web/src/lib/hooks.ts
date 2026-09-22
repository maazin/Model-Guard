import { useQuery } from "@tanstack/react-query";
import { useSyncExternalStore } from "react";
import { currentUser, get, subscribeUser } from "./api";
import type { Monitoring, VersionDetail } from "./types";

export const useVersion = (id: string | undefined) =>
  useQuery({ queryKey: ["version", id], queryFn: () => get<VersionDetail>(`/api/v1/model-versions/${id}`), enabled: !!id });

export const useMonitoring = (id: string | undefined) =>
  useQuery({ queryKey: ["monitoring", id], queryFn: () => get<Monitoring>(`/api/v1/model-versions/${id}/monitoring`), enabled: !!id });

export const useCurrentUser = () => useSyncExternalStore(subscribeUser, currentUser, currentUser);
