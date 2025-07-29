export const listen = jest.fn(() => ({ then: (cb) => cb(() => {}) }));
