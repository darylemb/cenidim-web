import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { Canciones } from './Canciones';
import { apiService } from '../services/api';
import React from 'react';

// Mock the api service completely
jest.mock('../services/api');

const mockSongs = [
  { id: 1, album: 'Vol. 2', title: 'La Cucaracha', filename: 'cuca.txt' },
  { id: 2, album: 'Vol. 1', title: 'Cielito Lindo', filename: 'cielito.txt' },
];

describe('Canciones Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test('renders with no results and shows empty state', () => {
    render(<Canciones results={[]} loading={false} handleReset={() => {}} />);

    expect(screen.getByText('Canciones')).toBeInTheDocument();
    expect(screen.getByText('No se encontraron resultados para su búsqueda.')).toBeInTheDocument();
  });

  test('renders song list when results are provided', () => {
    render(<Canciones results={mockSongs} loading={false} handleReset={() => {}} />);

    expect(screen.getByText('La Cucaracha')).toBeInTheDocument();
    expect(screen.getByText('Vol. 2')).toBeInTheDocument();
    expect(screen.getByText('cuca.txt')).toBeInTheDocument();
    expect(screen.getByText('Cielito Lindo')).toBeInTheDocument();
  });

  test('shows loading overlay when loading prop is true', () => {
    render(<Canciones results={[]} loading={true} handleReset={() => {}} />);

    expect(screen.getByText('Buscando en el archivo del CENIDIM...')).toBeInTheDocument();
  });

  test('renders safely with default props (no crash without props)', () => {
    render(<Canciones />);
    expect(screen.getByText('Canciones')).toBeInTheDocument();
  });

  test('opens lyrics modal when "Ver Letra" is clicked', async () => {
    apiService.getSongDetail.mockResolvedValueOnce({
      id: 1,
      title: 'La Cucaracha',
      album: 'Vol. 2',
      lyrics: 'La cucaracha, la cucaracha...',
    });

    render(<Canciones results={mockSongs} loading={false} handleReset={() => {}} />);

    const buttons = screen.getAllByText('Ver Letra');
    fireEvent.click(buttons[0]);

    await waitFor(() => {
      expect(screen.getByText('La cucaracha, la cucaracha...')).toBeInTheDocument();
    });
    expect(apiService.getSongDetail).toHaveBeenCalledWith(1);
  });
});
