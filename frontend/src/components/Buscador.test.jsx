import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Buscador } from './Buscador';
import { apiService } from '../services/api';
import React from 'react';

// Mock the api service completely
jest.mock('../services/api');

describe('Buscador Component', () => {
  beforeEach(() => {
    // Clear all instances and calls to constructor and all methods
    jest.clearAllMocks();
  });

  test('renders initial layout properly', async () => {
    // Mock default search response empty
    apiService.searchSongs.mockResolvedValueOnce([]);

    render(<Buscador />);

    expect(screen.getByText('Buscador')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Buscar...')).toBeInTheDocument();

    // Check for our custom loading state immediately
    expect(screen.getByText('Buscando en la base de datos...')).toBeInTheDocument();

    await waitFor(() => {
      expect(
        screen.getByText('No se encontraron resultados para su búsqueda.')
      ).toBeInTheDocument();
    });
  });

  test('performs search API call and renders songs correctly', async () => {
    const mockSongs = [{ id: 1, album: 'Vol. 2', title: 'La Cucaracha', filename: 'cuca.txt' }];

    // First call (on mount)
    apiService.searchSongs.mockResolvedValueOnce([]);
    // Second call (on explicit search)
    apiService.searchSongs.mockResolvedValueOnce(mockSongs);

    render(<Buscador />);

    // Wait for initial render to finish
    await waitFor(() => screen.getByText('No se encontraron resultados para su búsqueda.'));

    // Trigger search
    const searchInput = screen.getByPlaceholderText('Buscar...');
    const searchBtn = screen.getByText('Buscar');

    fireEvent.change(searchInput, { target: { value: 'Cucaracha' } });
    fireEvent.click(searchBtn);

    expect(screen.getByText('Buscando en la base de datos...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText('La Cucaracha')).toBeInTheDocument();
      expect(screen.getByText('Vol. 2')).toBeInTheDocument();
      expect(screen.getByText('cuca.txt')).toBeInTheDocument();
    });
  });
});
