import {render, screen} from '@testing-library/react';
import {describe, expect, it} from 'vitest';

import {StatusBadge} from '../src/components/StatusBadge';

describe('StatusBadge', () => {
  it('renders the label', () => {
    render(<StatusBadge tone="ok" label="Operational" />);

    expect(screen.getByText('Operational')).toBeInTheDocument();
  });

  it('exposes the tone for styling and testing', () => {
    render(<StatusBadge tone="degraded" label="Degraded" />);

    expect(screen.getByText('Degraded')).toHaveAttribute('data-tone', 'degraded');
  });
});
