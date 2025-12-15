import { create } from "zustand";

/* Cluster types  */

export interface ClusterStatistics {
  modularity?: number | null;
  silhouette?: number | null;
  conductance?: number | null;
  coverage?: number | null;
}

export interface ClusterData {
  nodes: any[];
  statistics?: ClusterStatistics;
  links?: any[];
}

/*  Metric types  */

export interface MetricData {
  nodes: any[];
}

/*  Dataset analysis  */

export type DatasetAnalysis = {
  clusters?: {
    leiden?: ClusterData;
    louvain?: ClusterData;
  };
  metrics?: {
    pagerank?: MetricData;
    betweenness?: MetricData;
  };
};

/*  Store  */

interface ParamsState {
  city: string;
  transport: string;
  analysisType: string;
  datasetId: string;

  datasetCache: Record<string, DatasetAnalysis>;

  clusterType: "leiden" | "louvain";
  metricType: "pagerank" | "betweenness";

  // setters
  setCity: (v: string) => void;
  setTransport: (v: string) => void;
  setAnalysisType: (v: string) => void;
  setDatasetId: (id: string) => void;
  setClusterType: (type: "leiden" | "louvain") => void;
  setMetricType: (type: "pagerank" | "betweenness") => void;

  setAnalysisData: (datasetId: string, analysis: DatasetAnalysis) => void;
  getAnalysisData: (datasetId: string) => DatasetAnalysis | undefined;

  setAll: (params: Partial<ParamsState>) => void;
  resetAnalysisData: () => void;
}

export const useParamsStore = create<ParamsState>((set, get) => ({
  city: "",
  transport: "",
  analysisType: "",
  datasetId: "",
  datasetCache: {},

  clusterType: "leiden",
  metricType: "pagerank",

  setCity: (city) => set({ city }),
  setTransport: (transport) => set({ transport }),
  setAnalysisType: (analysisType) => set({ analysisType }),
  setDatasetId: (datasetId) => set({ datasetId }),
  setClusterType: (clusterType) => set({ clusterType }),
  setMetricType: (metricType) => set({ metricType }),

  setAnalysisData: (datasetId, analysis) =>
    set((state) => ({
      datasetCache: {
        ...state.datasetCache,
        [datasetId]: analysis,
      },
    })),

  getAnalysisData: (datasetId) => get().datasetCache[datasetId],

  setAll: (params) => {
    if (params.city || params.transport) {
      const newCache = { ...get().datasetCache };
      if (get().datasetId) {
        delete newCache[get().datasetId];
      }
      set({
        ...params,
        datasetCache: newCache,
      });
    } else {
      set(params);
    }
  },

  resetAnalysisData: () => {
    const newCache = { ...get().datasetCache };
    if (get().datasetId) {
      delete newCache[get().datasetId];
    }
    set({
      datasetCache: newCache,
      clusterType: "leiden",
      metricType: "pagerank",
    });
  },
}));