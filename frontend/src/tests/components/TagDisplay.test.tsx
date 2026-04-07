import React from 'react';
import { render, screen } from '@testing-library/react';
import '@testing-library/jest-dom';
import { TagType } from '../../types/tag';
import TagDisplay from '../../components/TagDisplay';

describe('TagDisplay', () => {
  const mockTag: TagType = { 
    id: '1', 
    name: 'Python', 
    color: 'blue',
    description: 'A programming language'
  };

  it('renders tag name correctly', () => {
    render(<TagDisplay tag={mockTag} />);
    expect(screen.getByText('Python')).toBeInTheDocument();
  });

  it('applies correct color styling', () => {
    render(<TagDisplay tag={mockTag} />);
    const tagElement = screen.getByText('Python').closest('span');
    expect(tagElement).toHaveClass('bg-blue-100', 'text-blue-800');
  });

  it('applies additional className when provided', () => {
    render(<TagDisplay tag={mockTag} className="ml-2" />);
    const tagElement = screen.getByText('Python').closest('span');
    expect(tagElement).toHaveClass('ml-2');
  });

  it('matches snapshot', () => {
    const { container } = render(<TagDisplay tag={mockTag} />);
    expect(container).toMatchSnapshot();
  });
});