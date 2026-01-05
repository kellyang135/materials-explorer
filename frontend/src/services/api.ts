import axios from 'axios';
import { 
  Material, 
  MaterialsResponse, 
  SearchResponse, 
  Calculation,
  Structure,
  PredictResponse
} from '../types/api';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export class MaterialsAPI {
  static async getMaterials(page = 1, pageSize = 20): Promise<MaterialsResponse> {
    const response = await api.get('/materials', {
      params: { page, page_size: pageSize }
    });
    return response.data;
  }

  static async getMaterial(materialId: string): Promise<Material> {
    const response = await api.get(`/materials/${materialId}`);
    return response.data;
  }

  static async getMaterialCalculations(materialId: string): Promise<Calculation[]> {
    const response = await api.get(`/materials/${materialId}/calculations`);
    return response.data;
  }

  static async getMaterialStructure(materialId: string): Promise<Structure> {
    const response = await api.get(`/materials/${materialId}/structure`);
    return response.data;
  }

  static async searchMaterials(params: {
    query?: string;
    elements?: string;
    crystal_system?: string;
    page?: number;
    page_size?: number;
  }): Promise<SearchResponse> {
    const response = await api.get('/search', { params });
    return response.data;
  }

  static async predictProperties(structureData: {
    structure_json?: any;
    cif_string?: string;
    properties: string[];
  }): Promise<PredictResponse> {
    const response = await api.post('/predict', structureData);
    return response.data;
  }

  static async getAvailableModels(): Promise<any> {
    const response = await api.get('/predict/models');
    return response.data;
  }
}

export default MaterialsAPI;