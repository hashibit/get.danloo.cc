import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import MaterialCard from '../../components/MaterialCard';

describe('MaterialCard', () => {
  const mockMaterial = {
    id: 'material-1',
    title: 'Test Material',
    contentType: 'application/pdf',
    fileSize: 1024,
    createdAt: '2025-01-01T00:00:00Z',
    updatedAt: '2025-01-01T00:00:00Z',
  };

  const mockOnProcess = jest.fn();
  const mockOnView = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders material title correctly', () => {
    render(
      <MaterialCard
        {...mockMaterial}
        onProcess={mockOnProcess}
        onView={mockOnView}
      />
    );

    expect(screen.getByText('Test Material')).toBeInTheDocument();
  });

  it('renders content type correctly', () => {
    render(
      <MaterialCard
        {...mockMaterial}
        onProcess={mockOnProcess}
        onView={mockOnView}
      />
    );

    expect(screen.getByText('PDF文档')).toBeInTheDocument();
  });

  it('renders file size correctly', () => {
    render(
      <MaterialCard
        {...mockMaterial}
        onProcess={mockOnProcess}
        onView={mockOnView}
      />
    );

    expect(screen.getByText('1.0 KB')).toBeInTheDocument();
  });

  it('calls onProcess when process button is clicked', () => {
    render(
      <MaterialCard
        {...mockMaterial}
        onProcess={mockOnProcess}
        onView={mockOnView}
      />
    );

    const processButton = screen.getByText('Process');
    fireEvent.click(processButton);

    expect(mockOnProcess).toHaveBeenCalledWith('material-1');
  });

  it('calls onView when view button is clicked', () => {
    render(
      <MaterialCard
        {...mockMaterial}
        onProcess={mockOnProcess}
        onView={mockOnView}
      />
    );

    const viewButton = screen.getByText('View');
    fireEvent.click(viewButton);

    expect(mockOnView).toHaveBeenCalledWith('material-1');
  });
});